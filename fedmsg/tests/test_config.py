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
""" Tests for fedmsg.config """

import unittest
from nose.tools import eq_

import fedmsg.config
from common import load_config


class RecursiveUpdateBase(unittest.TestCase):
    originals = None
    expected = None

    def test_match(self):
        """ Does fedmsg.config._recursive_update produce the expected result?
        """

        if None in (self.originals, self.expected):
            return

        actual = dict()
        for o in self.originals:
            actual = fedmsg.config._recursive_update(actual, o)

        eq_(actual, self.expected)


class TestSimpleOne(RecursiveUpdateBase):
    originals = [dict(a=2)]
    expected = dict(a=2)


class TestSimpleTwo(RecursiveUpdateBase):
    originals = [
        dict(a=2),
        dict(b=3),
    ]
    expected = dict(a=2, b=3)


class TestOverwrite(RecursiveUpdateBase):
    originals = [
        dict(a=2),
        dict(a=3),
    ]
    expected = dict(a=3)


class TestMerge(RecursiveUpdateBase):
    originals = [
        dict(a=dict(a=2)),
        dict(a=dict(b=3)),
    ]
    expected = dict(a=dict(a=2, b=3))


class TestConfig(unittest.TestCase):
    """Test for try out the function iterate in
    endpoints config"""

    def test_config(self):
        config = load_config()
        endpoints = config['endpoints']

        for key, value in endpoints.iteritems():
            assert isinstance(value, list), value


if __name__ == '__main__':
    unittest.main()
