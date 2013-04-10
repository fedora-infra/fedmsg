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
import fedmsg
import logging

from fedmsg.consumers import FedmsgConsumer

log = logging.getLogger(__name__)


class RelayConsumer(FedmsgConsumer):
    config_key = 'fedmsg.consumers.relay.enabled'

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        # The consumer should pick up *all* messages.
        self.topic = self.hub.config.get('topic_prefix', 'org.fedoraproject')
        if not self.topic.endswith('*'):
            self.topic += '*'

        super(RelayConsumer, self).__init__(hub)

        self.validate_signatures = False

    def consume(self, msg):
        ## FIXME - for some reason twisted is screwing up fedmsg.
        #fedmsg.__context.publisher.send_multipart(
        #    [msg['topic'], fedmsg.encoding.dumps(msg['body'])]
        #)
        #
        # We have to do this instead.  This works for the fedmsg-relay service
        # since it doesn't need to do any formatting of the message.  It just
        # forwards raw messages.
        #
        # This isn't scalable though.  It needs to be solved for future
        # consumers to use the nice fedmsg.send_message interface we use
        # everywhere else.

        log.debug("Got message %r" % msg)
        self.hub.send_message(topic=msg['topic'], message=msg['body'])
