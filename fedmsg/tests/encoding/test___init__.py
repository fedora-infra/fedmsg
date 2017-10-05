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
"""Tests for the :mod:`fedmsg.encoding` module."""

import json
import unittest

from fedmsg.encoding import FedMsgEncoder


class FedMsgEncoderTests(unittest.TestCase):
    """Tests for the :class:`fedmsg.encoding.FedMsgEncoder`."""

    def test_default(self):
        """Assert normal types are encoded the same way as the default encoder."""
        self.assertEqual(json.dumps('a string'), json.dumps('a string', cls=FedMsgEncoder))

    def test_default_sets_to_lists(self):
        """Assert sets are converted to lists."""
        self.assertEqual(
            sorted(['a', 'set']), sorted(FedMsgEncoder().default(set(['a', 'a', 'set']))))

    def test_default_obj_with_json(self):
        """Assert classes with a ``__json__`` function encode as the return of ``__json__``."""

        class JsonClass(object):
            def __json__(self):
                return {'my': 'json'}

        self.assertEqual({'my': 'json'}, FedMsgEncoder().default(JsonClass()))
