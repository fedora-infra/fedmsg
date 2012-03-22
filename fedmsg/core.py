import atexit
import inspect
import simplejson
import time
import warnings
import zmq

import fedmsg.schema
import fedmsg.json


class FedMsgContext(object):
    def __init__(self, **config):
        super(FedMsgContext, self).__init__()

        self.c = config

        # Prepare our context and publisher
        self.context = zmq.Context(config['io_threads'])
        if config.get("publish_endpoint", None):
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(config["publish_endpoint"])
        elif config.get("relay", None):
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.connect(config["relay"])
        else:
            # fedmsg is not configured to send any messages
            #raise ValueError("FedMsgContext was misconfigured.")
            pass

        # Define and register a 'destructor'.
        def destructor():
            if hasattr(self, 'publisher'):
                self.publisher.close()

            self.context.term()

        atexit.register(destructor)

        # Sleep just to make sure that the socket gets set up before anyone
        # tries anything.  This is a documented zmq 'feature'.
        time.sleep(config['post_init_sleep'])

    def subscribe(self, topic, callback):
        raise NotImplementedError

    def send_message(self, topic=None, msg=None, modname=None):

        if not topic:
            warnings.warn("Attempted to send message with no topic.  Bailing.")
            return

        if not msg:
            warnings.warn("Attempted to send message with no msg.  Bailing.")
            return

        if not modname:
            # If no modname is supplied, then guess it from the call stack.
            frame = inspect.stack()[2][0]
            modname = frame.f_globals['__name__'].split('.')[0]

        topic = modname + '.' + topic

        if topic[:len(self.c['topic_prefix'])] != self.c['topic_prefix']:
            topic = self.c['topic_prefix'] + '.' + topic

        for key in msg.keys():
            if key not in fedmsg.schema.keys:
                warnings.warn("%r not one of %r" % (key, fedmsg.schema.keys))

        msg = {'topic': topic, 'msg': msg}
        self.publisher.send_multipart([topic, fedmsg.json.dumps(msg)])

    def have_pulses(self, endpoints, timeout):
        """
        Returns a dict of endpoint->bool mappings indicating which endpoints
        are emitting detectable heartbeats.
        """

        timeout = timeout / 1000.0
        topic = self.c['topic_prefix'] + '.heartbeat'
        subscribers = {}
        for endpoint in endpoints:
            subscriber = self.context.socket(zmq.SUB)
            subscriber.setsockopt(zmq.SUBSCRIBE, topic)
            subscriber.connect(endpoint)
            subscribers[endpoint] = subscriber

        results = dict(zip(endpoints, [False] * len(endpoints)))
        tic = time.time()
        while not all(results.values()) and (time.time() - tic) < timeout:
            for e in endpoints:
                if results[e]:
                    continue

                try:
                    subscribers[e].recv_multipart(zmq.NOBLOCK)
                    results[e] = True
                except zmq.ZMQError:
                    pass

        for endpoint in endpoints:
            subscribers[endpoint].close()

        return results
