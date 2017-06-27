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

"""Tests for the :mod:`fedmsg.commands.relay` module."""
from __future__ import absolute_import

import unittest

from moksha.hub import monitoring
import mock

from fedmsg.commands import relay


@mock.patch('fedmsg.commands.relay.main')
class RelayCommandTests(unittest.TestCase):
    """Tests for the plain ``fedmsg-relay`` command."""

    def setUp(self):
        with mock.patch.object(relay.RelayCommand, '__init__', mock.Mock(return_value=None)):
            self.command = relay.RelayCommand()
        self.command.config = {
            'relay_inbound': ['circus', 'of', 'values'],
            'endpoints': {'relay_outbound': ['some-socket']},
        }
        self.expected_config = self.command.config.copy()
        self.expected_config['zmq_subscribe_endpoints'] = 'circus,of,values'
        self.expected_config['zmq_subscribe_method'] = 'bind'
        self.expected_config['zmq_publish_endpoints'] = 'some-socket'
        self.expected_config['fedmsg.consumers.relay.enabled'] = True

    def test_config(self, mock_main):
        """Assert the configuration is modified as expected."""
        self.command.run()
        self.assertEqual(self.expected_config, self.command.config)

    def test_return_value(self, mock_main):
        """Assert the command returns the result of ``moksha.hub.main``."""
        result = self.command.run()
        self.assertTrue(result is mock_main.return_value)

    def test_main(self, mock_main):
        """Assert the command creates a monitoring producer and a relay consumer."""
        self.command.run()
        mock_main.assert_called_once_with(
            options=self.expected_config,
            consumers=[relay.RelayConsumer],
            producers=[monitoring.MonitoringProducer],
            framework=False,
        )
