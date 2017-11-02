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
"""The main interface for fedmsg."""
from __future__ import absolute_import
import logging
import json

import six
import zmq

from . import config, exceptions
from .broker.service import SUBMISSION_V1

_log = logging.getLogger(__name__)


def publish(topic=u'', headers=None, body=None, timeout=10):
    """
    Publish a fedmsg via the fedmsg broker service.

    This API blocks until the broker responses with either success or failure.

    Args:
        topic (str): A unicode string to use as the message topic. If ``topic_prefix``
            is set it will be prepended to this topic.
        headers (dict): Optional message headers.
        body (dict): A JSON-serializable dictionary.
        timeout (float, int): The time to wait, in seconds, for a response
            from the fedmsg broker. Set to -1 for infinite timeout.

    Raises:
        ValueError: If the topic is not a unicode string.
        exceptions.ReadTimeout: If there's no response from the broker. Note that
            the message could have been published even if this exception is raised.
        exceptions.WriteTimeout: If no connection can be established to the broker.

    Returns:
        list: The multi-part response from the broker.
    """
    if not isinstance(topic, six.text_type):
        raise ValueError('Message topic must be a unicode string')

    # -1 means block forever, don't multiply by 1000 to make it seconds
    if not timeout == -1:
        timeout *= 1000

    if headers is None:
        headers = {}

    if body is None:
        body = {}

    # Before sending the message over the wire, we need to encode it to bytes.
    # We don't allow a configurable encoding and force it to be utf-8.
    topic = topic.encode('utf-8')
    headers = json.dumps(headers).encode('utf-8')
    body = json.dumps(body).encode('utf-8')
    _log.info('Publishing message to the "%r" topic', topic)

    context = zmq.Context.instance()
    with context.socket(zmq.REQ) as request_socket:
        # Only queue messages for delivery if there's an active connection.
        # Failing to do this means the message lands in the local queue for
        # delivery and it's not clear to the user that the message got sent.
        request_socket.setsockopt(zmq.IMMEDIATE, 1)
        request_socket.setsockopt(zmq.RCVTIMEO, timeout)
        request_socket.setsockopt(zmq.SNDTIMEO, timeout)
        request_socket.connect(config.conf['submission_endpoint'])

        try:
            request_socket.send_multipart([SUBMISSION_V1, topic, headers, body])
        except zmq.Again:
            raise exceptions.WriteTimeout(
                'Unable to write to "{}" in {} milliseconds'.format(
                    config.conf['submission_endpoint'], timeout))
        try:
            return request_socket.recv_multipart()
        except zmq.Again:
            raise exceptions.ReadTimeout(
                'No response from the fedmsg broker at "{}" in {} seconds'.format(
                    config.conf['submission_endpoint'], timeout))
