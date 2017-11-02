# This file is part of fedmsg.
# Copyright (C) 2018 Red Hat, Inc.
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

import unittest

import zmq

from fedmsg.broker import publishers


class PublisherTests(unittest.TestCase):
    """Unit tests for the :class:`fedmsg.broker.publishers.Publisher` class."""

    def test_init(self):
        """Assert initialization binds to an inproc socket."""
        publisher = publishers.Publisher()

        self.assertEqual(publisher.pair.socket_type, zmq.PAIR)
        self.assertEqual('inproc://Publisher', publisher.pair_address)

    def test_publish(self):
        publisher = publishers.Publisher()
        self.assertRaises(NotImplementedError, publisher.publish, None, None, None)
