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

from fedmsg.consumers import FedmsgConsumer

import logging
log = logging.getLogger("moksha.hub")


class DummyConsumer(FedmsgConsumer):
    topic = "org.fedoraproject.*"
    config_key = 'fedmsg.consumers.dummy.enabled'

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        return super(DummyConsumer, self).__init__(hub)

    def consume(self, msg):
        # Do nothing.
        log.debug("Duhhhh... got: %r" % msg)
