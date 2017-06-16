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
import logging

from fedmsg.consumers import FedmsgConsumer
from fedmsg import crypto

log = logging.getLogger(__name__)


class RelayConsumer(FedmsgConsumer):
    config_key = 'fedmsg.consumers.relay.enabled'
    topic = '*'

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None

        super(RelayConsumer, self).__init__(hub)

        self.validate_signatures = False

    def consume(self, msg):
        # FIXME - for some reason twisted is screwing up fedmsg.
        # fedmsg.__context.publisher.send_multipart(
        #    [msg['topic'], fedmsg.encoding.dumps(msg['body'])]
        # )
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


class SigningRelayConsumer(RelayConsumer):
    """
    A relay that signs messages it relays with x509 certificates.

    The key pair used for message signing is configured by setting the ``signing_relay``
    key in the ``certnames`` configuration dictionary to the key pair name inside of
    the configured ``ssldir``. See the configuration documentation for more information.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the relay.

        All arguments are passed directly on to the :class:`RelayConsumer`.
        """
        super(SigningRelayConsumer, self).__init__(*args, **kwargs)

        try:
            self.hub.config['certname'] = self.hub.config['certnames']['signing_relay']
        except KeyError:
            log.error('The signing relay requires that the certificate name is in '
                      'the "certnames" dictionary using the "signing_relay" key')

    def consume(self, msg):
        """
        Sign the message prior to sending the message.

        Args:
            msg (dict): The message to sign and relay.
        """
        msg['body'] = crypto.sign(msg['body'], **self.hub.config)
        super(SigningRelayConsumer, self).consume(msg)
