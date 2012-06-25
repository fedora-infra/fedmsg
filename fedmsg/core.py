import atexit
import inspect
import simplejson
import socket
import time
import warnings
import zmq

from kitchen.text.converters import to_utf8

import fedmsg.json
import fedmsg.crypto


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
        if self.c.get('sign_messages', False):
            self.c['certname'] = self.c['certnames'][self.hostname]


        # Prepare our context and publisher
        self.context = zmq.Context(config['io_threads'])
        method = config.get('active', False) or 'bind' and 'connect'
        method = ['bind', 'connect'][config['active']]

        # If no name is provided, use the calling module's __name__ to decide
        # which publishing endpoint to use.
        if not config.get("name", None):
            config["name"] = self.guess_calling_module() + '.' + self.hostname

            if any(map(config["name"].startswith, ['__main__', 'fedmsg'])):
                config["name"] = None

        # Actually set up our publisher
        if config.get("name", None) and config.get("endpoints", None):
            self.publisher = self.context.socket(zmq.PUB)

            if config['high_water_mark']:
                self.publisher.setsockopt(zmq.HWM, config['high_water_mark'])

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

        else:
            warnings.warn("fedmsg is not configured to send any messages")

        atexit.register(self.destroy)

        # Sleep just to make sure that the socket gets set up before anyone
        # tries anything.  This is a documented zmq 'feature'.
        time.sleep(config['post_init_sleep'])

    def destroy(self):
        """ Destructor """
        if getattr(self, 'publisher', None):
            self.publisher.close()
            self.publisher = None

        if getattr(self, 'context', None):
            self.context.term()
            self.context = None

    def subscribe(self, topic, callback):
        raise NotImplementedError

    # TODO -- this should be in kitchen, not fedmsg
    def guess_calling_module(self):
        # Iterate up the call-stack and return the first new top-level module
        for frame in (f[0] for f in inspect.stack()):
            modname = frame.f_globals['__name__'].split('.')[0]
            if modname != "fedmsg":
                return modname

        # Otherwise, give up and just return our own module name.
        return "fedmsg"

    def send_message(self, topic=None, msg=None, modname=None):
        warnings.warn(".send_message is deprecated.",
                      warnings.DeprecationWarning)

        return self.publish(topic, msg, modname)

    def publish(self, topic=None, msg=None, modname=None):

        if not topic:
            warnings.warn("Attempted to send message with no topic.  Bailing.")
            return

        if not msg:
            warnings.warn("Attempted to send message with no msg.  Bailing.")
            return

        # If no modname is supplied, then guess it from the call stack.
        modname = modname or self.guess_calling_module()
        topic = '.'.join([modname, topic])

        if topic[:len(self.c['topic_prefix'])] != self.c['topic_prefix']:
            topic = '.'.join([
                self.c['topic_prefix'],
                self.c['environment'],
                topic,
            ])

        if type(topic) == unicode:
            topic = to_utf8(topic)

        self._i += 1
        msg = dict(topic=topic, msg=msg, timestamp=time.time(), i=self._i)

        if self.c.get('sign_messages', False):
            msg = fedmsg.crypto.sign(msg, **self.c)

        self.publisher.send_multipart([topic, fedmsg.json.dumps(msg)])

    def have_pulses(self, endpoints):
        """
        Generates a list of 3-tuples of the form (name, endpoint, bool) indicating
        which endpoints have detectable heartbeats.

        """

        topic = self.c['topic_prefix'] + '._heartbeat'

        # Initialize a nested dict of all False results.
        results = {}
        for name, ep_list in endpoints.items():
            results[name] = dict(zip(ep_list, [False] * len(ep_list)))

        tic = time.time()

        generator = self._tail_messages(
            endpoints, topic, timeout=self.c['timeout'])

        for name, ep, topic, msg in generator:
            if not results[name][ep]:
                yield name, ep, True

            results[name][ep] = True

            if all(results.values()) or \
               (time.time() - tic) < self.c['timeout']:
                break

        for name in results:
            for ep in results[name]:
                yield name, ep, False

    def _tail_messages(self, endpoints, topic="", passive=False, **kw):
        """
        Generator that yields messages on the bus in the form of tuples::

        >>> (endpoint, topic, message)
        """

        # TODO -- the 'passive' here and the 'active' are ambiguous.  They
        # don't actually mean the same thing.  This should be resolved.
        method = passive and 'bind' or 'connect'

        subs = {}
        for _name, endpoint_list in endpoints.iteritems():
            for endpoint in endpoint_list:
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
                        try:
                            _topic, message = \
                                    subs[e].recv_multipart(zmq.NOBLOCK)
                            tic = time.time()
                            yield _name, e, _topic, fedmsg.json.loads(message)
                        except zmq.ZMQError:
                            if timeout and (time.time() - tic) > timeout:
                                return
        finally:
            for _name, endpoint_list in endpoints.iteritems():
                for endpoint in endpoint_list:
                    subs[endpoint].close()
