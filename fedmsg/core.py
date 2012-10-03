# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
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
import socket
import threading
import time
import warnings
import weakref
import zmq

from kitchen.text.converters import to_bytes

import fedmsg.encoding
import fedmsg.crypto

import logging
log = logging.getLogger("fedmsg")


def _listify(obj):
    if not isinstance(obj, list):
        obj = [obj]

    return obj


class FedMsgContext(object):
    # A counter for messages sent.
    _i = 0

    def __init__(self, **config):
        super(FedMsgContext, self).__init__()

        self.c = config
        self.hostname = socket.gethostname().split('.', 1)[0]

        # Prepare our context and publisher
        self.context = zmq.Context(config['io_threads'])
        method = config.get('active', False) or 'bind' and 'connect'
        method = ['bind', 'connect'][config['active']]

        # If no name is provided, use the calling module's __name__ to decide
        # which publishing endpoint to use.
        if not config.get("name", None):
            module_name = self.guess_calling_module(default="fedmsg")
            config["name"] = module_name + '.' + self.hostname

            if any(map(config["name"].startswith, ['fedmsg'])):
                config["name"] = None

        # Find my message-signing cert if I need one.
        if self.c.get('sign_messages', False) and config.get("name"):
            if 'cert_prefix' in config:
                cert_index = "%s.%s" % (config['cert_prefix'], self.hostname)
            else:
                cert_index = config['name']
                if cert_index == 'relay_inbound':
                    cert_index = "shell.%s" % self.hostname

            self.c['certname'] = self.c['certnames'][cert_index]

        # Do a little special-case mangling.  We never want to "listen" to the
        # relay_inbound address, but in the special case that we want to emit
        # our messages there, we add it to the :term:`endpoints` dict so that
        # the code below where we "Actually set up our publisher" can be
        # simplified.  See Issue #37 - http://bit.ly/KN6dEK
        if config.get('active', False):
            # If the user has called us with "active=True" then presumably they
            # have given us a "name" as well.
            name = config.get("name", "relay_inbound")
            config['endpoints'][name] = config[name]

        # Actually set up our publisher
        if (
            not config.get("mute", False) and
            config.get("name", None) and
            config.get("endpoints", None) and
            config['endpoints'].get(config['name'])
        ):
            self.publisher = self.context.socket(zmq.PUB)

            if config['high_water_mark']:
                self.publisher.setsockopt(zmq.HWM, config['high_water_mark'])

            if method == 'connect':
                self.publisher.setsockopt(zmq.LINGER, config['zmq_linger'])

            config['endpoints'][config['name']] = _listify(
                config['endpoints'][config['name']])

            _established = False
            for endpoint in config['endpoints'][config['name']]:

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
                raise IOError("Couldn't find an available endpoint.")

        elif config.get('mute', False):
            # Our caller doesn't intend to send any messages.  Pass silently.
            pass
        else:
            # Something is wrong.
            warnings.warn("fedmsg is not configured to send any messages")

        # Cleanup.  See http://bit.ly/SaGeOr for discussion.
        weakref.ref(threading.current_thread(), self.destroy)

        # Sleep just to make sure that the socket gets set up before anyone
        # tries anything.  This is a documented zmq 'feature'.
        time.sleep(config['post_init_sleep'])

    def destroy(self):
        """ Destroy a fedmsg context """

        if getattr(self, 'publisher', None):
            self.publisher.close()
            self.publisher = None

        if getattr(self, 'context', None):
            self.context.term()
            self.context = None

    # TODO -- this should be in kitchen, not fedmsg
    def guess_calling_module(self, default=None):
        # Iterate up the call-stack and return the first new top-level module
        for frame in (f[0] for f in inspect.stack()):
            modname = frame.f_globals['__name__'].split('.')[0]
            if modname != "fedmsg":
                return modname

        # Otherwise, give up and just return the default.
        return default

    def send_message(self, topic=None, msg=None, modname=None):
        warnings.warn(".send_message is deprecated.",
                      warnings.DeprecationWarning)

        return self.publish(topic, msg, modname)

    def publish(self, topic=None, msg=None, modname=None):
        """ Send a message over the publishing zeromq socket.

          >>> import fedmsg
          >>> fedmsg.publish(topic='testing', modname='test', msg={
          ...     'test': "Hello World",
          ... })

        The above snippet will send the message ``'{test: "Hello World"}'``
        over the ``org.fedoraproject.dev.test.testing`` topic.

        This function (and other API functions) do a little bit more
        heavy lifting than they let on.  If the "zeromq context" is not yet
        initialized, :func:`fedmsg.init` is called to construct it and
        store it as :data:`fedmsg.__local.__context` before anything else is
        done.

        The ``modname`` argument will be omitted in most use cases.  By
        default, ``fedmsg`` will try to guess the name of the module that
        called it and use that to produce an intelligent topic.  Specifying
        ``modname`` explicitly overrides this behavior.

        The fully qualified topic of a message is constructed out of the
        following pieces:

         <:term:`topic_prefix`>.<:term:`environment`>.<``modname``>.<``topic``>

        ----

        **An example from Fedora Tagger -- SQLAlchemy encoding**

        Here's an example from
        `fedora-tagger <http://github.com/ralphbean/fedora-tagger>`_ that
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

        if not topic:
            warnings.warn("Attempted to send message with no topic.  Bailing.")
            return

        if not msg:
            warnings.warn("Attempted to send message with no msg.  Bailing.")
            return

        # If no modname is supplied, then guess it from the call stack.
        modname = modname or self.guess_calling_module(default="fedmsg")
        topic = '.'.join([modname, topic])

        if topic[:len(self.c['topic_prefix'])] != self.c['topic_prefix']:
            topic = '.'.join([
                self.c['topic_prefix'],
                self.c['environment'],
                topic,
            ])

        if type(topic) == unicode:
            topic = to_bytes(topic, encoding='utf8', nonstring="passthru")

        self._i += 1
        msg = dict(topic=topic, msg=msg, timestamp=time.time(), i=self._i)

        if self.c.get('sign_messages', False):
            msg = fedmsg.crypto.sign(msg, **self.c)

        self.publisher.send_multipart(
            [topic, fedmsg.encoding.dumps(msg)],
            flags=zmq.NOBLOCK,
        )

    def tail_messages(self, endpoints, topic="", passive=False, **kw):
        """ Tail messages on the bus.

        Generator that yields tuples of the form:
        ``(name, endpoint, topic, message)``
        """

        # TODO -- the 'passive' here and the 'active' are ambiguous.  They
        # don't actually mean the same thing.  This should be resolved.
        method = passive and 'bind' or 'connect'

        failed_hostnames = []
        subs = {}
        for _name, endpoint_list in endpoints.iteritems():
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
                        log.warn("Couldn't resolve %r" % hostname)
                        continue

                # OK, sanity checks pass.  Create the subscriber and connect.
                subscriber = self.context.socket(zmq.SUB)
                subscriber.setsockopt(zmq.SUBSCRIBE, topic)
                getattr(subscriber, method)(endpoint)
                subs[endpoint] = subscriber

        timeout = kw['timeout']
        tic = time.time()
        try:
            while True:
                for _name, endpoint_list in endpoints.iteritems():
                    for e in endpoint_list:
                        if e not in subs:
                            continue
                        try:
                            _topic, message = \
                                    subs[e].recv_multipart(zmq.NOBLOCK)
                            tic = time.time()
                            encoded = fedmsg.encoding.loads(message)
                            yield _name, e, _topic, encoded
                        except zmq.ZMQError:
                            if timeout and (time.time() - tic) > timeout:
                                return
        finally:
            for endpoint, subscriber in subs.items():
                subscriber.close()
