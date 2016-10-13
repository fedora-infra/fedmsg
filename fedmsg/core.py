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

import getpass
import socket
import threading
import datetime
import six
import time
import uuid
import warnings
import weakref
import zmq

from kitchen.iterutils import iterate
from kitchen.text.converters import to_bytes

import fedmsg.encoding
import fedmsg.crypto

from fedmsg.utils import (
    set_high_water_mark,
    guess_calling_module,
    set_tcp_keepalive,
    set_tcp_reconnect,
)

from fedmsg.replay import check_for_replay

import logging


class ValidationError(Exception):
    """ Error used internally to represent a validation failure. """
    def __init__(self, msg):
        self.msg = msg


class FedMsgContext(object):
    # A counter for messages sent.
    _i = 0

    def __init__(self, **config):
        super(FedMsgContext, self).__init__()
        self.log = logging.getLogger("fedmsg")

        self.c = config
        self.hostname = socket.gethostname().split('.', 1)[0]

        # Prepare our context and publisher
        self.context = zmq.Context(config['io_threads'])
        method = ['bind', 'connect'][config['active']]

        # If no name is provided, use the calling module's __name__ to decide
        # which publishing endpoint to use (unless active=True, in which case
        # we use "relay_inbound" as set in the subsequent code block).
        if not config.get("name", None) and not config.get('active', False):
            module_name = guess_calling_module(default="fedmsg")
            config["name"] = module_name + '.' + self.hostname

            if any(map(config["name"].startswith, ['fedmsg'])):
                config["name"] = None

        # Do a little special-case mangling.  We never want to "listen" to the
        # relay_inbound address, but in the special case that we want to emit
        # our messages there, we add it to the :term:`endpoints` dict so that
        # the code below where we "Actually set up our publisher" can be
        # simplified.  See Issue #37 - https://bit.ly/KN6dEK
        if config.get('active', False):
            try:
                name = config['name'] = config.get("name", "relay_inbound")
                config['endpoints'][name] = config[name]
            except KeyError:
                raise KeyError("Could not find endpoint for fedmsg-relay."
                              " Try installing fedmsg-relay.")

        # Actually set up our publisher, but only if we're configured for zmq.
        if (
            config.get('zmq_enabled', True) and
            not config.get("mute", False) and
            config.get("name", None) and
            config.get("endpoints", None) and
            config['endpoints'].get(config['name'])
        ):
            # Construct it.
            self.publisher = self.context.socket(zmq.PUB)

            set_high_water_mark(self.publisher, config)
            set_tcp_keepalive(self.publisher, config)

            # Set a zmq_linger, thus doing a little bit more to ensure that our
            # message gets to the fedmsg-relay (*if* we're talking to the relay
            # which is the case when method == 'connect').
            if method == 'connect':
                self.publisher.setsockopt(zmq.LINGER, config['zmq_linger'])

            # "Listify" our endpoints.  If we're given a list, good.  If we're
            # given a single item, turn it into a list of length 1.
            config['endpoints'][config['name']] = list(iterate(
                config['endpoints'][config['name']]))

            # Try endpoint after endpoint in the list of endpoints.  If we
            # succeed in establishing one, then stop.  *That* is our publishing
            # endpoint.
            _established = False
            for endpoint in config['endpoints'][config['name']]:
                self.log.debug("Trying to %s to %s" % (method, endpoint))
                if method == 'bind':
                    endpoint = "tcp://*:{port}".format(
                        port=endpoint.rsplit(':')[-1]
                    )

                try:
                    # Call either bind or connect on the new publisher.
                    # This will raise an exception if there's another process
                    # already using the endpoint.
                    getattr(self.publisher, method)(endpoint)
                    # If we can do this successfully, then stop trying.
                    _established = True
                    break
                except zmq.ZMQError:
                    # If we fail to bind or connect, there's probably another
                    # process already using that endpoint port.  Try the next
                    # one.
                    pass

            # If we make it through the loop without establishing our
            # connection, then there are not enough endpoints listed in the
            # config for the number of processes attempting to use fedmsg.
            if not _established:
                raise IOError(
                    "Couldn't find an available endpoint "
                    "for name %r" % config.get("name", None))

        elif config.get('mute', False):
            # Our caller doesn't intend to send any messages.  Pass silently.
            pass
        elif config.get('zmq_enabled', True):
            # Something is wrong.
            warnings.warn(
                "fedmsg is not configured to send any zmq messages "
                "for name %r" % config.get("name", None))
        else:
            # We're not configured to send zmq messages, but zmq_enabled is
            # False, so no need to warn the user.
            pass

        # Cleanup.  See https://bit.ly/SaGeOr for discussion.
        weakref.ref(threading.current_thread(), self.destroy)

        # Sleep just to make sure that the socket gets set up before anyone
        # tries anything.  This is a documented zmq 'feature'.
        time.sleep(config['post_init_sleep'])

    def destroy(self):
        """ Destroy a fedmsg context """

        if getattr(self, 'publisher', None):
            self.log.debug("closing fedmsg publisher")
            self.publisher.close()
            self.publisher = None

        if getattr(self, 'context', None):
            self.context.term()
            self.context = None

    def send_message(self, topic=None, msg=None, modname=None):
        warnings.warn(".send_message is deprecated.", DeprecationWarning)

        return self.publish(topic, msg, modname)

    def publish(self, topic=None, msg=None, modname=None,
                pre_fire_hook=None, **kw):
        """ Send a message over the publishing zeromq socket.

          >>> import fedmsg
          >>> fedmsg.publish(topic='testing', modname='test', msg={
          ...     'test': "Hello World",
          ... })

        The above snippet will send the message ``'{test: "Hello World"}'``
        over the ``<topic_prefix>.dev.test.testing`` topic.

        This function (and other API functions) do a little bit more
        heavy lifting than they let on.  If the "zeromq context" is not yet
        initialized, :func:`fedmsg.init` is called to construct it and
        store it as :data:`fedmsg.__local.__context` before anything else is
        done.

        The ``modname`` argument will be omitted in most use cases.  By
        default, ``fedmsg`` will try to guess the name of the module that
        called it and use that to produce an intelligent topic.  Specifying
        ``modname`` explicitly overrides this behavior.

        The ``pre_fire_hook`` argument may be a callable that will be called
        with a single argument -- the dict of the constructed message -- just
        before it is handed off to ZeroMQ for publication.

        The fully qualified topic of a message is constructed out of the
        following pieces:

         <:term:`topic_prefix`>.<:term:`environment`>.<``modname``>.<``topic``>

        ----

        **An example from Fedora Tagger -- SQLAlchemy encoding**

        Here's an example from
        `fedora-tagger <https://github.com/fedora-infra/fedora-tagger>`_ that
        sends the information about a new tag over
        ``org.fedoraproject.{dev,stg,prod}.fedoratagger.tag.update``::

          >>> import fedmsg
          >>> fedmsg.publish(topic='tag.update', msg={
          ...     'user': user,
          ...     'tag': tag,
          ... })

        Note that the `tag` and `user` objects are SQLAlchemy objects defined
        by tagger.  They both have ``.__json__()`` methods which
        :func:`fedmsg.publish` uses to encode both objects as stringified
        JSON for you.  Under the hood, specifically, ``.publish`` uses
        :mod:`fedmsg.encoding` to do this.

        ``fedmsg`` has also guessed the module name (``modname``) of it's
        caller and inserted it into the topic for you.  The code from which
        we stole the above snippet lives in
        ``fedoratagger.controllers.root``.  ``fedmsg`` figured that out and
        stripped it down to just ``fedoratagger`` for the final topic of
        ``org.fedoraproject.{dev,stg,prod}.fedoratagger.tag.update``.

        ----

        **Shell Usage**

        You could also use the ``fedmsg-logger`` from a shell script like so::

            $ echo "Hello, world." | fedmsg-logger --topic testing
            $ echo '{"foo": "bar"}' | fedmsg-logger --json-input

        """

        topic = topic or 'unspecified'
        msg = msg or dict()

        # If no modname is supplied, then guess it from the call stack.
        modname = modname or guess_calling_module(default="fedmsg")
        topic = '.'.join([modname, topic])

        if topic[:len(self.c['topic_prefix'])] != self.c['topic_prefix']:
            topic = '.'.join([
                self.c['topic_prefix'],
                self.c['environment'],
                topic,
            ])

        if isinstance(topic, six.text_type):
            topic = to_bytes(topic, encoding='utf8', nonstring="passthru")

        year = datetime.datetime.now().year

        self._i += 1
        msg = dict(
            topic=topic.decode('utf-8'),
            msg=msg,
            timestamp=int(time.time()),
            msg_id=str(year) + '-' + str(uuid.uuid4()),
            i=self._i,
            username=getpass.getuser(),
        )

        # Find my message-signing cert if I need one.
        if self.c.get('sign_messages', False):
            if not self.c.get("crypto_backend") == "gpg":
                if 'cert_prefix' in self.c:
                    cert_index = "%s.%s" % (self.c['cert_prefix'],
                                            self.hostname)
                else:
                    cert_index = self.c['name']
                    if cert_index == 'relay_inbound':
                        cert_index = "shell.%s" % self.hostname

                self.c['certname'] = self.c['certnames'][cert_index]
            else:
                if 'gpg_signing_key' not in self.c:
                    self.c['gpg_signing_key'] = self.c['gpg_keys'][self.hostname]

        if self.c.get('sign_messages', False):
            msg = fedmsg.crypto.sign(msg, **self.c)

        store = self.c.get('persistent_store', None)
        if store:
            # Add the seq_id field
            msg = store.add(msg)

        if pre_fire_hook:
            pre_fire_hook(msg)

        # We handle zeromq publishing ourselves.  But, if that is disabled,
        # defer to the moksha' hub's twisted reactor to send messages (if
        # available).
        if self.c.get('zmq_enabled', True):
            self.publisher.send_multipart(
                [topic, fedmsg.encoding.dumps(msg).encode('utf-8')],
                flags=zmq.NOBLOCK,
            )
        else:
            # Perhaps we're using STOMP or AMQP?  Let moksha handle it.
            import moksha.hub
            # First, a quick sanity check.
            if not moksha.hub._hub:
                raise AttributeError("Unable to publish non-zeromq msg"
                                     "without moksha-hub initialization.")
            # Let moksha.hub do our work.
            moksha.hub._hub.send_message(
                topic=topic,
                message=fedmsg.encoding.dumps(msg).encode('utf-8'),
                jsonify=False,
            )


    def tail_messages(self, topic="", passive=False, **kw):
        """ Tail messages on the bus.

        Generator that yields tuples of the form:
        ``(name, endpoint, topic, message)``
        """

        if not self.c.get('zmq_enabled', True):
            raise ValueError("fedmsg.tail_messages() is only available for "
                             "zeromq.  Use the hub-consumer approach for "
                             "STOMP or AMQP support.")

        poller, subs = self._create_poller(topic=topic, passive=False, **kw)
        try:
            for msg in self._poll(poller, subs):
                yield msg
        finally:
            self._close_subs(subs)

    def _create_poller(self, topic="", passive=False, **kw):
        # TODO -- do the zmq_strict logic dance with "topic" here.
        # It is buried in moksha.hub, but we need it to work the same way
        # here.

        # TODO -- the 'passive' here and the 'active' are ambiguous.  They
        # don't actually mean the same thing.  This should be resolved.
        method = passive and 'bind' or 'connect'

        failed_hostnames = []
        subs = {}
        for _name, endpoint_list in six.iteritems(self.c['endpoints']):

            # You never want to actually subscribe to this thing, but sometimes
            # it appears in the endpoints list due to a hack where it gets
            # added in __init__ above.
            if _name == 'relay_inbound':
                continue

            # Listify endpoint_list in case it is a single string
            endpoint_list = iterate(endpoint_list)
            for endpoint in endpoint_list:
                # First, some sanity checking.  zeromq will potentially
                # segfault if we don't do this check.
                hostname = endpoint.split(':')[1][2:]
                if hostname in failed_hostnames:
                    continue

                if hostname != '*':
                    try:
                        socket.gethostbyname_ex(hostname)
                    except:
                        failed_hostnames.append(hostname)
                        self.log.warn("Couldn't resolve %r" % hostname)
                        continue

                # OK, sanity checks pass.  Create the subscriber and connect.
                subscriber = self.context.socket(zmq.SUB)
                subscriber.setsockopt(zmq.SUBSCRIBE, topic.encode('utf-8'))

                set_high_water_mark(subscriber, self.c)
                set_tcp_keepalive(subscriber, self.c)
                set_tcp_reconnect(subscriber, self.c)

                getattr(subscriber, method)(endpoint)
                subs[subscriber] = (_name, endpoint)

        # Register the sockets we just built with a zmq Poller.
        poller = zmq.Poller()
        for subscriber in subs:
            poller.register(subscriber, zmq.POLLIN)

        return (poller, subs)

    def _poll(self, poller, subs):
        watched_names = {}
        for name, _ in subs.values():
            if name in self.c.get("replay_endpoints", {}):
                # At first we don't know where the sequence is at.
                watched_names[name] = -1

        # Poll that poller.  This is much more efficient than it used to be.
        while True:
            sockets = dict(poller.poll())
            for s in sockets:
                name, ep = subs[s]
                try:
                    yield self._run_socket(s, name, ep, watched_names)
                except ValidationError as e:
                    warnings.warn("!! invalid message received: %r" % e.msg)

    def _run_socket(self, sock, name, ep, watched_names=None):
        if watched_names is None:
            watched_names = {}

        validate = self.c.get('validate_signatures', False)

        # Grab the data off the zeromq internal queue
        _topic, message = sock.recv_multipart()

        # zmq hands us byte strings, so let's convert to unicode asap
        _topic, message = _topic.decode('utf-8'), message.decode('utf-8')

        # Now, decode the JSON body into a dict.
        msg = fedmsg.encoding.loads(message)

        if not validate or fedmsg.crypto.validate(msg, **self.c):
            # If there is even a slight change of replay, use
            # check_for_replay
            if len(self.c.get('replay_endpoints', {})) > 0:
                for m in check_for_replay(
                        name, watched_names,
                        msg, self.c, self.context):

                    # Revalidate all the replayed messages.
                    if not validate or \
                            fedmsg.crypto.validate(m, **self.c):
                        return name, ep, m['topic'], m
                    else:
                        raise ValidationError(msg)
            else:
                return name, ep, _topic, msg
        else:
            raise ValidationError(msg)

    def _close_subs(self, subs):
            for subscriber in subs:
                subscriber.close()
