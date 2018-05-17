# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#

import inspect
import json
import logging
import os
import psutil
import requests
import threading
import time
import warnings

import moksha.hub.api.consumer
import six

import fedmsg.crypto
import fedmsg.encoding
from fedmsg.replay import check_for_replay


class FedmsgConsumer(moksha.hub.api.consumer.Consumer):
    """
    Base class for fedmsg consumers.

    This class inherits from :class:`moksha.hub.api.consumer.Consumer` and you
    should familiarize yourself with this class as well.

    To create a consumer, you must inherit this class and do the following:

        * Declare the class on the ``moksha.consumers`` python entry-point::

              setup(
                  entry_points={
                      'moksha.consumer': (
                          'your_consumer = python.path:YourConsumerClass',
                      ),
                  },
              )

        * Implement the ``consume(self, message)`` method on the class.

        * Set the attributes documented below

    Attributes:
        validate_signatures (bool): If ``False``, message authenticity will not be
            checked. This is helpful if you're developing or building a special-case
            consumer. For example, the consumer used by :ref:`command-relay` sets
            ``validate_signatures = False`` so that it can transparently forward along
            everything and let the terminal endpoints decide whether or not to consume
            particular messages.

        topic (str or list): This attribute is required. Either a :class:`str`
            or :class:`list` of :class:`str` that are topics that this consumer
            is interested in receiving messages for. To receive all messages, use
            an empty string.

        config_key (str): The name of the configuration key used to enable or disable
            this consumer. If this key is not present in the fedmsg configuration or
            does not have a value of ``True``, :ref:`command-hub` will not run the
            consumer.

        replay_name (str): The name of the replay endpoint where the system should
            query for playback in case of missed messages. It must match a service
            key in :ref:`conf-replay-endpoints`. This attribute is optional.

    Args:
        hub (moksha.hub.hub.MokshaCentralHub): The Moksha Hub that is initializing this
            consumer.
    """

    validate_signatures = None
    config_key = None

    def __init__(self, hub):
        module = inspect.getmodule(self).__name__
        name = self.__class__.__name__
        self.log = logging.getLogger(__name__)

        if not self.config_key:
            raise ValueError("%s:%s must declare a 'config_key'" % (
                module, name))

        self.log.debug("%s is %r" % (
            self.config_key, hub.config.get(self.config_key)
        ))

        if not hub.config.get(self.config_key, False):
            self.log.info('* disabled by config - %s:%s' % (module, name))
            return

        self.log.info('  enabled by config  - %s:%s' % (module, name))

        # This call "completes" registration of this consumer with the hub.
        super(FedmsgConsumer, self).__init__(hub)

        # Now, re-get our logger to override the one moksha assigns us.
        self.log = logging.getLogger(__name__)

        if self.validate_signatures is None:
            self.validate_signatures = self.hub.config['validate_signatures']

        if hasattr(self, "replay_name"):
            self.name_to_seq_id = {}
            if self.replay_name in self.hub.config.get("replay_endpoints", {}):
                self.name_to_seq_id[self.replay_name] = -1

        # Check if we have a status file to see if we have a backlog or not.
        # Create its directory if it doesn't exist.
        self.status_directory = self.hub.config.get('status_directory')
        self.status_filename, self.status_lock = None, None
        if self.status_directory:

            # Extract proc name and handle differences between py2.6 and py2.7
            proc_name = current_proc().name
            if callable(proc_name):
                proc_name = proc_name()

            self.status_filename = os.path.join(
                self.status_directory, proc_name, type(self).__name__)

            topmost_directory, _ = self.status_filename.rsplit('/', 1)
            if not os.path.exists(topmost_directory):
                os.makedirs(topmost_directory)

        self.datagrepper_url = self.hub.config.get('datagrepper_url')
        if self.status_filename and self.datagrepper_url:
            # First, try to read in the status from a previous run and fire off
            # a thread to set up our workload.
            self.log.info("Backlog handling setup.  status: %r, url: %r" % (
                self.status_filename, self.datagrepper_url))
            self.status_lock = threading.Lock()
            try:
                with self.status_lock:
                    with open(self.status_filename, 'r') as f:
                        data = f.read()
                moksha.hub.reactor.reactor.callInThread(self._backlog, data)
            except IOError as e:
                self.log.info(e)
        else:
            self.log.info("No backlog handling.  status: %r, url: %r" % (
                self.status_filename, self.datagrepper_url))

    def _backlog(self, data):
        """Find all the datagrepper messages between 'then' and 'now'.

        Put those on our work queue.

        Should be called in a thread so as not to block the hub at startup.
        """

        try:
            data = json.loads(data)
        except ValueError as e:
            self.log.info("Status contents are %r" % data)
            self.log.exception(e)
            self.log.info("Skipping backlog retrieval.")
            return

        last = data['message']['body']
        if isinstance(last, str):
            last = json.loads(last)

        then = last['timestamp']
        now = int(time.time())

        retrieved = 0
        for message in self.get_datagrepper_results(then, now):
            # Take the messages from datagrepper and remove any keys that were
            # artificially added to the message.  The presence of these would
            # otherwise cause message crypto validation to fail.
            message = fedmsg.crypto.utils.fix_datagrepper_message(message)

            if message['msg_id'] != last['msg_id']:
                retrieved = retrieved + 1
                self.incoming.put(dict(body=message, topic=message['topic']))
            else:
                self.log.warning("Already seen %r; Skipping." % last['msg_id'])

        self.log.info("Retrieved %i messages from datagrepper." % retrieved)

    def get_datagrepper_results(self, then, now):
        def _make_query(page=1):
            return requests.get(self.datagrepper_url, params=dict(
                rows_per_page=100, page=page, start=then, end=now, order='asc'
            )).json()

        # Grab the first page of results
        data = _make_query()

        # Grab and smash subsequent pages if there are any
        interesting_topics = self.topic
        if not isinstance(interesting_topics, list):
            interesting_topics = [interesting_topics]

        for page in range(1, data['pages'] + 1):
            self.log.info("Retrieving datagrepper page %i of %i" % (
                page, data['pages']))
            data = _make_query(page=page)

            for message in data['raw_messages']:
                for topic in interesting_topics:
                    if message['topic'].startswith(topic[:-1]):
                        yield message
                        break

    def validate(self, message):
        """
        Validate the message before the consumer processes it.

        This needs to raise an exception, caught by moksha.

        Args:
            message (dict): The message as a dictionary. This must, at a minimum,
                contain the 'topic' key with a unicode string value and 'body' key
                with a dictionary value. However, the message might also be an object
                with a ``__json__`` method that returns a dict with a 'body' key that
                can be a unicode string that is JSON-encoded.

        Raises:
            RuntimeWarning: If the message is not valid.
            UnicodeDecodeError: If the message body is not unicode or UTF-8 and also
                happens to contain invalid UTF-8 binary.
        """
        if hasattr(message, '__json__'):
            message = message.__json__()
            if isinstance(message['body'], six.text_type):
                message['body'] = json.loads(message['body'])
            elif isinstance(message['body'], six.binary_type):
                # Try to decode the message body as UTF-8 since it's very likely
                # that that was the encoding used. This API should eventually only
                # accept unicode strings inside messages. If a UnicodeDecodeError
                # happens, let that bubble up.
                warnings.warn('Message body is not unicode', DeprecationWarning)
                message['body'] = json.loads(message['body'].decode('utf-8'))

        # Massage STOMP messages into a more compatible format.
        if 'topic' not in message['body']:
            message['body'] = {
                'topic': message.get('topic'),
                'msg': message['body'],
            }

        # If we're not validating, then everything is valid.
        # If this is turned on globally, our child class can override it.
        if not self.validate_signatures:
            return

        # We assume these match inside fedmsg.crypto, so we should enforce it.
        if not message['topic'] == message['body']['topic']:
            raise RuntimeWarning("Topic envelope mismatch.")

        if not fedmsg.crypto.validate(message['body'], **self.hub.config):
            raise RuntimeWarning("Failed to authn message.")

    def _consume(self, message):
        """ Called when a message is consumed.

        This private method handles some administrative setup and teardown
        before calling the public interface `consume` typically implemented
        by a subclass.

        When `moksha.blocking_mode` is set to `False` in the config, this
        method always returns `None`.  The argued message is stored in an
        internal queue where the consumer's worker threads should eventually
        pick it up.

        When `moksha.blocking_mode` is set to `True` in the config, this
        method should return True or False, indicating whether the message
        was handled or not.  Specifically, in the event that the inner
        `consume` method raises an exception of any kind, this method
        should return `False` indicating that the message was not
        successfully handled.

        Args:
            message (dict): The message as a dictionary.

        Returns:
            bool: Should be interpreted as whether or not the message was
            handled by the consumer, or `None` if `moksha.blocking_mode` is
            set to False.
        """

        try:
            self.validate(message)
        except RuntimeWarning as e:
            self.log.warn("Received invalid message {0}".format(e))
            return

        # Pass along headers if present.  May be useful to filters or
        # fedmsg.meta routines.
        if isinstance(message, dict) and 'headers' in message and 'body' in message:
            message['body']['headers'] = message['headers']

        if hasattr(self, "replay_name"):
            for m in check_for_replay(
                    self.replay_name, self.name_to_seq_id,
                    message, self.hub.config):

                try:
                    self.validate(m)
                    return super(FedmsgConsumer, self)._consume(m)
                except RuntimeWarning as e:
                    self.log.warn("Received invalid message {}".format(e))
        else:
            return super(FedmsgConsumer, self)._consume(message)

    def pre_consume(self, message):
        self.save_status(dict(
            message=message,
            status='pre',
        ))

    def post_consume(self, message):
        self.save_status(dict(
            message=message,
            status='post',
        ))

    def save_status(self, data):
        if self.status_filename and self.status_lock:
            with self.status_lock:
                with open(self.status_filename, 'w') as f:
                    f.write(fedmsg.encoding.dumps(data))


def current_proc():
    mypid = os.getpid()

    for proc in psutil.process_iter():
        if proc.pid == mypid:
            return proc

    # This should be impossible.
    raise ValueError("Could not find process %r" % mypid)
