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
import threading
import weakref
import zmq

from fedmsg.consumers import FedmsgConsumer


class GatewayConsumer(FedmsgConsumer):
    config_key = 'fedmsg.consumers.gateway.enabled'
    jsonify = False
    topic = '*'

    def __init__(self, hub):
        self.hub = hub

        super(GatewayConsumer, self).__init__(hub)

        # If fedmsg doesn't think we should be enabled, then we should quit
        # before setting up all the extra special zmq machinery.
        # _initialized is set in moksha.api.hub.consumer
        if not getattr(self, "_initialized", False):
            return

        self.port = hub.config['fedmsg.consumers.gateway.port']
        self.validate_signatures = False
        self._setup_special_gateway_socket()

        # Register a destructor?  This might be a bad idea inside Twisted.
        weakref.ref(threading.current_thread(), self.destroy)

    def _setup_special_gateway_socket(self):
        self.log.info("Setting up special gateway socket on " +
                      "port %r" % self.port)
        self._context = zmq.Context(1)
        self.gateway_socket = self._context.socket(zmq.PUB)

        # Set this to an absurdly high number to increase the number of clients
        # we can serve.  To be effective, also increase nofile for fedmsg in
        # /etc/security/limits.conf to near fs.file-limit.  Try 160000.
        hwm = self.hub.config['fedmsg.consumers.gateway.high_water_mark']
        if hasattr(zmq, 'HWM'):
            # zeromq2
            self.gateway_socket.setsockopt(zmq.HWM, hwm)
        else:
            # zeromq3
            self.gateway_socket.setsockopt(zmq.SNDHWM, hwm)
            self.gateway_socket.setsockopt(zmq.RCVHWM, hwm)

        self.gateway_socket.bind("tcp://*:{port}".format(port=self.port))
        self.log.info("Gateway socket established.")

    def destroy(self):
        self.log.info("Destroying GatewayConsumer")
        if getattr(self, 'gateway_socket', None):
            self.gateway_socket.close()
            self.gateway_socket = None

        if getattr(self, '_context', None):
            self._context.term()
            self._context = None

    def consume(self, msg):
        self.log.debug("Gateway: %r" % msg.topic)
        self.gateway_socket.send_multipart([
            msg.topic.encode('utf-8'),
            msg.body.encode('utf-8'),
        ])
