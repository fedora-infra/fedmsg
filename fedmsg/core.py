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
        super(FedMsgContext, self).__init__(**kw)

        # Prepare our context and publisher
        self.context = zmq.Context(1)
        self.publisher = self.context.socket(zmq.PUB)
        self.publisher.bind(kw.get("publish_endpoint", "tcp://*:6543"))

        # Define and register a 'destructor'.
        def destructor():
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
