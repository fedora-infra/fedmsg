import fedmsg

from paste.deploy.converters import asbool
from moksha.api.hub.consumer import Consumer

import logging
log = logging.getLogger("moksha.hub")


class DummyConsumer(Consumer):
    topic = "org.fedoraproject.*"

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        if not asbool(hub.config.get('fedmsg.consumers.dummy.enabled', False)):
            log.info('fedmsg.consumers.dummy:DummyConsumer disabled.')
            return

        return super(DummyConsumer, self).__init__(hub)

    def consume(self, msg):
        # Do nothing.
        log.debug("Duhhhh... got: %r" % msg)
