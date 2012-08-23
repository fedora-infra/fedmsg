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
import fedmsg.crypto
import moksha.api.hub.consumer

import logging
log = logging.getLogger("moksha.hub")


class FedmsgConsumer(moksha.api.hub.consumer.Consumer):
    validate_signatures = False
    config_key = None

    def __init__(self, hub):
        module = inspect.getmodule(self).__name__
        name = self.__class__.__name__

        if not self.config_key:
            raise ValueError("%s:%s must declare a 'config_key'" % (
                module, name))

        log.debug("%s is %r" % (
            self.config_key, hub.config.get(self.config_key)
        ))

        if not hub.config.get(self.config_key, False):
            log.info('* disabled by config - %s:%s' % (module, name))
            return

        log.info('  enabled by config  - %s:%s' % (module, name))

        # This call "completes" registration of this consumer with the hub.
        super(FedmsgConsumer, self).__init__(hub)

        self.validate_signatures = self.hub.config.get('validate_signaturs')

    def validate(self, message):
        """ This needs to raise an exception, caught by moksha. """

        # If we're not validating, then everything is valid.
        # If this is turned on globally, our child class can override it.
        if not self.validate_signatures:
            return

        if not fedmsg.crypto.validate(message['body'], **self.hub.config):
            raise RuntimeWarning("Failed to authn message.")
