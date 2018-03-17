# -*- coding: utf-8 -*-
#
# This file is part of fedmsg.
# Copyright (C) 2017 Red Hat, Inc.
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
# Authors:  Jeremy Cline <jcline@redhat.com>
"""Tests for the :mod:`fedmsg.consumers` module."""

import json
import os
import unittest

from moksha.hub.zeromq.zeromq import ZMQMessage
import mock

from fedmsg import crypto
from fedmsg.consumers import FedmsgConsumer
from fedmsg.tests.base import SSLDIR, FIXTURES_DIR


class DummyConsumer(FedmsgConsumer):
    """Set attributes necessary to instantiate a consumer."""
    config_key = 'dummy'
    validate_signatures = True


class FedmsgConsumerReplayTests(unittest.TestCase):
    """Tests for the replay functionality of fedmsg consumers method."""

    def setUp(self):
        self.config = {
            'dummy': True,
            'ssldir': SSLDIR,
            'ca_cert_location': os.path.join(SSLDIR, 'fedora_ca.crt'),
            'crl_location': None,
            'crypto_validate_backends': ['x509'],
        }
        self.hub = mock.Mock(config=self.config)
        self.consumer = DummyConsumer(self.hub)

    def test_backlog_message_validation(self):
        """Assert messages fetched from datanommer pass signature validation."""
        with open(os.path.join(FIXTURES_DIR, 'sample_datanommer_response.json')) as fd:
            replay_messages = json.load(fd)
        self.consumer.get_datagrepper_results = mock.Mock(
            return_value=replay_messages['raw_messages'])
        last_message = json.dumps({'message': {'body': {'msg_id': 'myid', 'timestamp': 0}}})

        # This places all the messages from a call to "get_datagrepper_results" in the
        # "incoming" queue.Queue
        self.consumer._backlog(last_message)

        while not self.consumer.incoming.empty():
            self.consumer.validate(self.consumer.incoming.get())


class FedmsgConsumerValidateTests(unittest.TestCase):
    """Tests for the :meth:`FedmsgConsumer.validate` method."""

    def setUp(self):
        self.config = {
            'dummy': True,
            'ssldir': SSLDIR,
            'certname': 'shell-app01.phx2.fedoraproject.org',
            'ca_cert_location': os.path.join(SSLDIR, 'ca.crt'),
            'crl_location': os.path.join(SSLDIR, 'crl.pem'),
            'crypto_validate_backends': ['x509'],
        }
        self.hub = mock.Mock(config=self.config)
        self.consumer = DummyConsumer(self.hub)

    def test_topic_mismatch(self):
        """Assert a RuntimeWarning is raised for topic mismatches."""
        message = {'topic': 't1', 'body': {'topic': 't2'}}

        self.assertRaises(RuntimeWarning, self.consumer.validate, message)

    def test_valid_signature(self):
        """Assert the API accepts and validates dictionary messages."""
        message = {'topic': 't1', 'body': crypto.sign({'topic': 't1'}, **self.config)}

        self.consumer.validate(message)

    def test_invalid_signature(self):
        """Assert a RuntimeWarning is raised for topic mismatches."""
        message = {'topic': 't1', 'body': crypto.sign({'topic': 't1'}, **self.config)}
        message['body']['signature'] = 'thisisnotmysignature'

        self.assertRaises(RuntimeWarning, self.consumer.validate, message)

    def test_no_topic_in_body(self):
        """Assert an empty topic is placed in the message if the key is missing."""
        self.consumer.validate_signatures = False
        message = {'body': {'some': 'stuff'}}

        self.consumer.validate(message)
        self.assertEqual({'body': {'topic': None, 'msg': {'some': 'stuff'}}}, message)

    @mock.patch('fedmsg.consumers.fedmsg.crypto.validate')
    def test_zmqmessage_text_body(self, mock_crypto_validate):
        self.consumer.validate_signatures = True
        self.consumer.hub.config = {}
        message = ZMQMessage(u't1', u'{"some": "stuff"}')

        self.consumer.validate(message)
        mock_crypto_validate.assert_called_once_with({'topic': u't1', 'msg': {'some': 'stuff'}})

    @mock.patch('fedmsg.consumers.warnings.warn')
    @mock.patch('fedmsg.consumers.fedmsg.crypto.validate')
    def test_zmqmessage_binary_body(self, mock_crypto_validate, mock_warn):
        self.consumer.validate_signatures = True
        self.consumer.hub.config = {}
        message = ZMQMessage(u't1', b'{"some": "stuff"}')

        self.consumer.validate(message)
        mock_crypto_validate.assert_called_once_with({'topic': u't1', 'msg': {'some': 'stuff'}})
        mock_warn.assert_any_call('Message body is not unicode', DeprecationWarning)


class FedmsgConsumerHandleTests(unittest.TestCase):
    """Tests for the :meth:`FedmsgConsumer._consume` method."""

    def setUp(self):
        self.config = {
            'dummy': True,
        }
        self.hub = mock.Mock(config=self.config)
        self.consumer = DummyConsumer(self.hub)

    def test_return_value_positive(self):
        self.consumer.validate_signatures = False
        self.consumer.blocking_mode = True
        self.consumer.hub.config = {}
        message = ZMQMessage(u't1', u'{"some": "stuff"}')

        # Consumer does nothing, no exception, returns True : handled.
        with mock.patch.object(self.consumer, 'consume'):
            handled = self.consumer._consume(message)
        assert handled is True

    def test_return_value_negative(self):
        self.consumer.validate_signatures = False
        self.consumer.blocking_mode = True
        self.consumer.hub.config = {}
        message = ZMQMessage(u't1', u'{"some": "stuff"}')

        # Consumer is unimplemented, and so raises and exception,
        # returning False : unhandled.
        handled = self.consumer._consume(message)
        assert handled is False
