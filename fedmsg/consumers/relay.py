import fedmsg

from paste.deploy.converters import asbool
from moksha.api.hub.consumer import Consumer

import logging
log = logging.getLogger("moksha.hub")


class RelayConsumer(Consumer):
    topic = "org.fedoraproject.*"

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        if not asbool(hub.config.get('fedmsg.consumers.relay.enabled', False)):
            log.info('fedmsg.consumers.relay:RelayConsumer disabled.')
            return

        return super(RelayConsumer, self).__init__(hub)

    def consume(self, msg):
        # FIXME - for some reason twisted is screwing up fedmsg.
        fedmsg.__context.publisher.send_multipart(
            [msg['topic'], fedmsg.json.dumps(msg['body'])]
        )
