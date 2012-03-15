import atexit
import inspect
import simplejson
import time
import warnings
import zmq

import fedmsg.schema
import fedmsg.json

TOPIC_PREFIX = "org.fedoraproject."


class FedMsgContext(object):
    def __init__(self, **kw):
        super(FedMsgContext, self).__init__()

        self.subscription_endpoints = kw.get('subscription_endpoints', [])

        # Prepare our context and publisher
        # '1' is the number of io_threads.  Make this configurable.
        self.context = zmq.Context(1)
        if kw.get("publish_endpoint", None):
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.bind(kw["publish_endpoint"])
        elif kw.get("relay", None):
            self.publisher = self.context.socket(zmq.PUB)
            self.publisher.connect(kw["relay"])
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
        time.sleep(1)

    def subscribe(self, topic, callback, **kw):
        raise NotImplementedError

    def send_message(self, topic, msg, guess_modname=True, **kw):

        if guess_modname:
            frame = inspect.stack()[2][0]
            modname = frame.f_globals['__name__'].split('.')[0]
            topic = modname + '.' + topic

        if topic[:len(TOPIC_PREFIX)] != TOPIC_PREFIX:
            topic = TOPIC_PREFIX + topic

        for key in msg.keys():
            if key not in fedmsg.schema.keys:
                warnings.warn("%r not one of %r" % (key, fedmsg.schema.keys))

        self.publisher.send_multipart([topic, fedmsg.json.dumps(msg)])

    def have_pulses(self, endpoints, timeout, **kw):
        """
        Returns a dict of endpoint->bool mappings indicating which endpoints
        are emitting detectable heartbeats.
        """

        timeout = timeout / 1000.0
        topic = TOPIC_PREFIX + 'heartbeat'
        subscribers = {}
        for endpoint in endpoints:
            subscriber = self.context.socket(zmq.SUB)
            subscriber.setsockopt(zmq.SUBSCRIBE, topic)
            subscriber.connect(endpoint)
            subscribers[endpoint] = subscriber

        results = dict(zip(endpoints, [False]*len(endpoints)))
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
