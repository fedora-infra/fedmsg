# -*- coding: utf-8 -*-
#
# This file is part of fedmsg.
# Copyright (C) 2017 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
"""
The fedmsg broker service.

The broker binds to a submission port and relays incoming messages to publishers
which are responsible for publishing the message to the world via ZeroMQ, AMQP,
carrier pigeon, etc.
"""
from __future__ import absolute_import

import logging
import json
import os
import signal

import zmq

from .publishers import ZeroMqPublisher, LegacyZeroMqPublisher


SUBMISSION_V1 = b'FSUBMIT1'
ERROR_MALFORMED = b'ERROR_MALFORMED'

_log = logging.getLogger(__name__)


class BrokerService(object):
    """
    The fedmsg broker service.

    This service binds to the given submission socket using a ZeroMQ Reply socket
    where clients can send publishing requests using a ZeroMQ Request socket. When
    all publishers have announced success or failure, the client is informed.

    The fedmsg submission message is a multi-part message that builds on top of
    the ZeroMQ `REQREP`_ RFC. The message should be made up of 4 data frames:

        * Frame 0: The fedmsg submission protocol version string. This is an ASCII-encoded
          string that indicates the protocol version being used. There is currently only
          one version, "FSUBMIT1".
        * Frame 1: The message topic as a UTF-8-encoded string.
        * Frame 2: A set of key-value pairs to use as the message headers. This should be
          a JSON-serialized object encoded with UTF-8.
        * Frame 3: The message body as a JSON-serialized object encoded with UTF-8.


    .. _REQREP: https://rfc.zeromq.org/spec:28/REQREP

    Args:
        submission_socket (str): A ZeroMQ socket to bind to for message submission.
        publisher_configs (list): A list of dictionaries containing publisher configurations.
        context (zmq.Context): The ZeroMQ context to use when creating sockets. If one is
            not provided, one will be created.
    """
    # Map config names to classes
    _publishers = {
        'zmq': ZeroMqPublisher,
        'legacy_zmq': LegacyZeroMqPublisher,
    }

    def __init__(self, submission_endpoint, publisher_configs, context=None):
        self.run = False
        self.context = context or zmq.Context.instance()
        self.submission_endpoint = submission_endpoint
        self.submission_socket = self.context.socket(zmq.REP)
        self.submission_socket.setsockopt(zmq.RCVTIMEO, 1500)

        # Create the publishers and their pair sockets
        self.publishers = [
            (self._publishers[name](context=self.context, **conf), self.context.socket(zmq.PAIR))
            for name, conf in publisher_configs.items() if name in self._publishers
        ]

    def start(self):
        """
        Start the fedmsg broker.

        This will block until the process receives a SIGINT or SIGTERM signal.
        """
        _log.info('Starting the fedmsg broker service')
        if self.submission_endpoint.startswith('ipc://'):
            socket_dir = os.path.dirname(self.submission_endpoint.split('ipc://')[1])
            if not os.path.exists(socket_dir):
                _log.info('%s does not exist, creating it for the submission endpoint', socket_dir)
                os.makedirs(socket_dir, mode=0o775)
        _log.info('Binding to %s as the fedmsg publisher submission socket',
                  self.submission_endpoint)
        self.submission_socket.bind(self.submission_endpoint)

        # Since this method blocks, let users halt us with a signal handler
        def _handler(signum, frame):
            """
            Signal handler that gracefully shuts down the broker.

            Args:
                signum (int): The signal this process received.
                frame (frame): The current stack frame (unused).
            """
            if signum in (signal.SIGTERM, signal.SIGINT):
                _log.info('Halting the fedmsg broker service')
                self.running = False

        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)

        self.running = True
        for pub, sock in self.publishers:
            pub.start()
            sock.connect(pub.pair_address)
        _log.info('fedmsg broker started successfully')

        self._run()

    def _run(self):
        """
        The main service loop.

        This loop is halted when the SIGINT/SIGTERM signal is received and handled.
        """
        while self.running:
            try:
                multipart_message = self.submission_socket.recv_multipart()
                _log.debug('Received message submission: %r', multipart_message)
            except zmq.Again:
                # The socket as a receive timeout of 1.5 seconds so we can check
                # to see if we've been asked to halt.
                continue

            if len(multipart_message) != 4 or multipart_message[0] != SUBMISSION_V1:
                # Later we can switch on the submission version to allow for graceful
                # handling of protocol changes.
                _log.error('The submitted message, "%r", is malformed', multipart_message)
                self.submission_socket.send_multipart([SUBMISSION_V1, ERROR_MALFORMED])
                continue

            for _, publish_pair in self.publishers:
                publish_pair.send_multipart(multipart_message[1:])
                _log.info('Sent message to %s', _)
            results = []
            for publisher, publish_pair in self.publishers:
                result = publish_pair.recv()
                results.append(json.loads(result.decode('utf-8')))
                _log.info('%s finished publishing and reported %s', publisher, result)
            self.submission_socket.send_multipart(
                [SUBMISSION_V1, json.dumps(results).encode('utf-8')])

        self._close()

    def _close(self, timeout=15):
        """
        Close all the sockets and shut down the publishers.

        Each publisher runs in a daemon thread so even if they don't successfully
        join we can halt, although this doesn't guarantee a clean shutdown.

        Args:
            timeout (float): The amount of time in seconds to wait on the thread
                to join. Setting this to ``None`` will cause this method to block
                (potentially indefinitely) until all threads close.
        """
        self.submission_socket.close()
        for pub, sock in self.publishers:
            _log.info('Signaling the %r publisher to shut down', pub)
            sock.send(b'HALT')
            pub.join(timeout=timeout)
            if pub.is_alive():
                _log.error('The %r publisher failed to halt after %r seconds, '
                           'shutting down forcibly!', pub, timeout)
            sock.close()
        _log.info('Halted the fedmsg broker')
