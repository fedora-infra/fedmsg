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
The fedmsg publishers.

fedmsg publishers accept messages from the publishing service and are responsible
for sending the message over ZeroMQ, AMQP, carrier pigeon, etc.
"""
from __future__ import absolute_import

import logging
import json
import threading

import zmq

_log = logging.getLogger(__name__)


class Publisher(threading.Thread):
    """
    The base class for fedmsg publishers.

    Each publisher should implement the interface defined by this class.
    """

    def __init__(self, context=None, **kwargs):
        """
        Publishers should perform any setup required to publish messages here. It
        is acceptable to use blocking APIs during the setup.

        Args:
            context (zmq.Context): The ZeroMQ context to use when creating the
                pair socket. If one is not provided, the default instance is used.
            **kwargs: The configuration settings for the publisher. The keys passed
                depend on the publisher. Users will be able to set the configuration
                in the fedmsg configuration file.
        """
        super(Publisher, self).__init__()
        self.daemon = True
        context = context or zmq.Context.instance()
        self.pair = context.socket(zmq.PAIR)
        self.pair_address = 'inproc://' + type(self).__name__
        self.pair.bind(self.pair_address)

    def run(self):
        """
        Receive messages to send over the ZeroMQ pair socket and hand them to the
        :meth:`publish` method. Sub-classes should not need to override this method.
        """
        while True:
            try:
                topic, headers, body = self.pair.recv_multipart()
            except ValueError as e:
                _log.error('Unable to unpack message from pair socket: %s', e)
                continue
            try:
                topic = topic.decode('utf-8')
                headers = headers.decode('utf-8')
                body = body.decode('utf-8')
                if len(headers):
                    headers = json.loads(headers)
                if len(body):
                    body = json.loads(body)
            except (ValueError, UnicodeDecodeError) as e:
                _log.exception('Unable to decode message %r; not sending via %s',
                               [topic, headers, body], type(self).__name__)
                continue

            try:
                self.publish(topic, headers, body)
                result = {'publisher': type(self).__name__, 'result': 'success', 'reason': None}
            except Exception as e:
                _log.exception('An unexpected exception occurred publishing %r via %s',
                               [topic, headers, body], type(self).__name__)
                result = {'publisher': type(self).__name__, 'result': 'failure', 'reason': str(e)}

            self.pair.send(json.dumps(result).encode('utf-8'))

    def publish(self, topic, headers, body):
        """
        This method is called when a message is submitted by a user for publication.

        How the topic, headers, and body are published are dependent on the type
        of publisher.

        Each :class:`Publisher` runs in a separate Python thread and should block until the
        message delivery has been either confirmed or failed with the configured timeout.

        Args:
            topic (six.text_type): The ZeroMQ topic this message was sent to as a unicode string.
                This may contain any unicode character and implementations must account for that.
            headers (dict): A set of message headers. Each key and value will be a unicode string.
            body (dict): The message body.
        """
        raise NotImplementedError


class ZeroMqPublisher(Publisher):
    """
    Publisher that sends messages via a ZeroMQ PUB socket.

    Args:
        context (zmq.Context): The ZeroMQ context to use when creating the
            pair socket. If one is not provided, the default instance is used.
        publish_endpoint (str): The endpoint to bind the publishing socket to in
            standard ZeroMQ format ('tcp://127.0.0.1:9940', 'ipc:///path/to/sock', etc).
    """

    publisher_version = b'FEDPUB1'

    def __init__(self, context=None, publish_endpoint=None):
        super(ZeroMqPublisher, self).__init__(context=context)

        context = context or zmq.Context.instance()
        self.publish_endpoint = publish_endpoint
        self.pub_socket = context.socket(zmq.PUB)
        _log.info('Binding to %s for ZeroMQ publication', publish_endpoint)
        self.pub_socket.bind(publish_endpoint)

    def publish(self, topic, headers, body):
        """
        Publish messages to a ZeroMQ PUB socket.

        Args:
            topic (six.text_type): The ZeroMQ topic this message was sent to as a unicode string.
                This may contain any unicode character and implementations must account for that.
            headers (dict): A set of message headers. Each key and value will be a unicode string.
            body (dict): The message body.
        """

        _log.info('Publishing message on "%s" to the ZeroMQ PUB socket "%s"',
                  topic, self.publish_endpoint)
        topic = topic.encode('utf-8')
        headers = json.dumps(headers).encode('utf-8')
        body = json.dumps(body).encode('utf-8')
        multipart_message = [topic, self.publisher_version, headers, body]
        self.pub_socket.send_multipart(multipart_message)


class LegacyZeroMqPublisher(ZeroMqPublisher):
    """
    Publisher that sends messages via a ZeroMQ PUB socket using the v1 fedmsg
    wire format.

    Args:
        context (zmq.Context): The ZeroMQ context to use when creating the
            pair socket. If one is not provided, the default instance is used.
        publish_endpoint (str): The endpoint to bind the publishing socket to in
            standard ZeroMQ format ('tcp://127.0.0.1:9940', 'ipc:///path/to/sock', etc).
    """

    def publish(self, topic, headers, body):
        """
        Publish messages to a ZeroMQ PUB socket in the legacy format.

        The legacy format is a two part message over a PUB socket - the first
        is the topic and the second is an arbitrary JSON object.

        Args:
            topic (six.text_type): The ZeroMQ topic this message was sent to as a unicode string.
                This may contain any unicode character and implementations must account for that.
            headers (dict): A set of message headers. Each key and value will be a unicode string.
            body (dict): The message body.
        """

        _log.info('Publishing message on "%s" to the ZeroMQ PUB socket "%s"',
                  topic, self.publish_endpoint)
        topic = topic.encode('utf-8')
        # There were no headers in the first version of fedmsg, they got placed in the body
        body[u'headers'] = headers
        body = json.dumps(body).encode('utf-8')
        multipart_message = [topic, body]
        self.pub_socket.send_multipart(multipart_message)
