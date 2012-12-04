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
""" Tests for fedmsg.meta """

import unittest
from nose.tools import eq_

import fedmsg.meta

from common import load_config


class Base(unittest.TestCase):
    msg = None
    expected_title = None
    expected_subti = None
    expected_link = None
    expected_icon = None
    expected_secondary_icon = None
    expected_usernames = set()
    expected_packages = set()
    expected_objects = set()

    def setUp(self):
        self.config = fedmsg.config.load_config(None, None,
                                                invalidate_cache=True)
        fedmsg.meta.make_processors(**self.config)

    def test_title(self):
        """ Does fedmsg.meta produce the expected title? """
        if None in (self.msg, self.expected_title):
            return
        actual_title = fedmsg.meta.msg2title(self.msg, **self.config)
        eq_(actual_title, self.expected_title)

    def test_subtitle(self):
        """ Does fedmsg.meta produce the expected subtitle? """
        if None in (self.msg, self.expected_subti):
            return
        actual_subti = fedmsg.meta.msg2subtitle(self.msg, **self.config)
        eq_(actual_subti, self.expected_subti)

    def test_link(self):
        """ Does fedmsg.meta produce the expected link? """
        if None in (self.msg, self.expected_link):
            return
        actual_link = fedmsg.meta.msg2link(self.msg, **self.config)
        eq_(actual_link, self.expected_link)

    def test_icon(self):
        """ Does fedmsg.meta produce the expected icon? """
        if None in (self.msg, self.expected_icon):
            return
        actual_icon = fedmsg.meta.msg2icon(self.msg, **self.config)
        eq_(actual_icon, self.expected_icon)

    def test_secondary_icon(self):
        """ Does fedmsg.meta produce the expected secondary icon? """
        if None in (self.msg, self.expected_secondary_icon):
            return
        actual_icon = fedmsg.meta.msg2secondary_icon(self.msg, **self.config)
        eq_(actual_icon, self.expected_secondary_icon)

    def test_usernames(self):
        """ Does fedmsg.meta produce the expected list of usernames? """
        if self.msg is None:
            return
        actual_usernames = fedmsg.meta.msg2usernames(self.msg, **self.config)
        eq_(actual_usernames, self.expected_usernames)

    def test_packages(self):
        """ Does fedmsg.meta produce the expected list of packages? """
        if self.msg is None:
            return
        actual_packages = fedmsg.meta.msg2packages(self.msg, **self.config)
        eq_(actual_packages, self.expected_packages)

    def test_objects(self):
        """ Does fedmsg.meta produce the expected list of objects? """
        if self.msg is None:
            return
        actual_objects = fedmsg.meta.msg2objects(self.msg, **self.config)
        eq_(actual_objects, self.expected_objects)


class TestUnhandled(Base):
    expected_title = "unhandled_service.some_event (unsigned)"
    expected_subti = ""
    msg = {
        "topic": "org.fedoraproject.stg.unhandled_service.some_event"
    }


class TestAnnouncement(Base):
    expected_title = "announce.announcement (unsigned)"
    expected_subti = 'hello, world.'
    expected_link = 'foo'
    expected_usernames = set(['ralph'])

    msg = {
        "i": 1,
        "timestamp": 1344352873.714926,
        "topic": "org.fedoraproject.dev.announce.announcement",
        "msg": {
            "message": "hello, world.",
            "link": "foo",
        },
        'username': 'ralph',
    }


class TestLoggerNormal(Base):
    expected_title = "logger.log (unsigned)"
    expected_subti = 'hello, world.'
    expected_usernames = set(['ralph'])

    msg = {
        "i": 1,
        "timestamp": 1344352873.714926,
        "topic": "org.fedoraproject.dev.logger.log",
        "msg": {
            "log": "hello, world."
        },
        'username': 'ralph',
    }


class TestLoggerJSON(Base):
    expected_title = "logger.log (unsigned)"
    expected_subti = '<custom JSON message>'
    expected_usernames = set(['root'])

    msg = {
        "i": 1,
        "timestamp": 1344352929.415939,
        "topic": "org.fedoraproject.dev.logger.log",
        "msg": {
            "foo": "bar"
        },
        'username': 'root',
    }


if __name__ == '__main__':
    unittest.main()
