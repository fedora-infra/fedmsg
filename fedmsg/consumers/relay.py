import fedmsg

from paste.deploy.converters import asbool
from fedmsg.consumers import FedmsgConsumer

import logging
log = logging.getLogger("moksha.hub")


class RelayConsumer(FedmsgConsumer):
    topic = "org.fedoraproject.*"

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        if not asbool(hub.config.get('fedmsg.consumers.relay.enabled', False)):
            log.info('fedmsg.consumers.relay:RelayConsumer disabled.')
            return

        super(RelayConsumer, self).__init__(hub)

        self.validate_messages = False


    def consume(self, msg):
        ## FIXME - for some reason twisted is screwing up fedmsg.
        #fedmsg.__context.publisher.send_multipart(
        #    [msg['topic'], fedmsg.json.dumps(msg['body'])]
        #)
        #
        # We have to do this instead.  This works for the fedmsg-relay service
        # since it doesn't need to do any formatting of the message.  It just
        # forwards raw messages.
        #
        # This isn't scalable though.  It needs to be solved for future
        # consumers to use the nice fedmsg.send_message interface we use
        # everywhere else.

        self.hub.send_message(topic=msg['topic'], message=msg['body'])
