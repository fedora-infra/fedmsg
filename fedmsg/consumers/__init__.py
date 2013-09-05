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
import moksha.hub.api.consumer
import json

import logging

from fedmsg.replay import check_for_replay


class FedmsgConsumer(moksha.hub.api.consumer.Consumer):
    """ Base class for fedmsg consumers.

    The fedmsg consumption API is really just a thin wrapper over moksha.
    Moksha expects consumers to:

        * Declare themselves on the moksha.consumers python entry-point.
        * Declare a ``consume(...)`` method.
        * Specify a ``topic``.

    All this class does in addition to moksha is:

        * Provide a mechanism for disabling/enabling consumers by configuration
          in a consistent way (namely, by use of ``config_key``).

          If you set ``validate_signatures = False`` on your consumer, it will
          be exempt from global validation rules.  Messages will not be
          checked for authenticity before being handed off to your consume
          method.  This is handy if you're developing or building a
          special-case consumer.  The consumer used by ``fedmsg-relay``
          (described in :doc:`commands`) sets ``validate_signatures = False``
          so that it can transparently forward along everything and let the
          terminal endpoints decide whether or not to consume particular
          messages.

        * Provide a mechanism for automatically validating fedmsg messages
          with :mod:`fedmsg.crypto`.

        * Provide a mechanism to play back messages that haven't been received
          by the hub even though emitted. To make use of this feature, you have
          to set ``replay_name`` to some string corresponding to an endpoint in
          the ``replay_endpoints`` dict in the configuration.

          You must set ``config_key`` to some string.  A config value by
          that name must be True in the config parsed by :mod:`fedmsg.config`
          in order for the consumer to be activated.
    """

    validate_signatures = False
    config_key = None

    def __init__(self, hub):
        module = inspect.getmodule(self).__name__
        name = self.__class__.__name__
        self.log = logging.getLogger("fedmsg")

        if not self.config_key:
            raise ValueError("%s:%s must declare a 'config_key'" % (
                module, name))

        self.log.debug("%s is %r" % (
            self.config_key, hub.config.get(self.config_key)
        ))

        if not hub.config.get(self.config_key, False):
            self.log.info('* disabled by config - %s:%s' % (module, name))
            return

        self.log.info('  enabled by config  - %s:%s' % (module, name))

        # This call "completes" registration of this consumer with the hub.
        super(FedmsgConsumer, self).__init__(hub)

        # Now, re-get our logger to override the one moksha assigns us.
        self.log = logging.getLogger("fedmsg")

        if self.validate_signatures:
            self.validate_signatures = self.hub.config['validate_signatures']
        if hasattr(self, "replay_name"):
            self.name_to_seq_id = {}
            if self.replay_name in self.hub.config.get("replay_endpoints", {}):
                self.name_to_seq_id[self.replay_name] = -1

    def validate(self, message):
        """ This needs to raise an exception, caught by moksha. """

        if hasattr(message, '__json__'):
            message = message.__json__()
            if isinstance(message['body'], basestring):
                message['body'] = json.loads(message['body'])

        # We assume these match inside fedmsg.crypto, so we should enforce it.
        if not message['topic'] == message['body']['topic']:
            raise RuntimeWarning("Topic envelope mismatch.")

        # If we're not validating, then everything is valid.
        # If this is turned on globally, our child class can override it.
        if not self.validate_signatures:
            return

        if not fedmsg.crypto.validate(message['body'], **self.hub.config):
            raise RuntimeWarning("Failed to authn message.")

    def _consume(self, message):
        try:
            self.validate(message)
        except RuntimeWarning as e:
            self.log.warn("Received invalid message {}".format(e))
            return
        if hasattr(self, "replay_name"):
            for m in check_for_replay(
                    self.replay_name, self.name_to_seq_id,
                    message, self.hub.config):

                try:
                    self.validate(m)
                    self.consume(m)
                except RuntimeWarning as e:
                    self.log.warn("Received invalid message {}".format(e))
        else:
            self.consume(message)
