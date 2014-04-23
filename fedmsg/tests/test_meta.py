# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
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

import os
import unittest

from nose import SkipTest
from nose.tools import eq_

try:
    from nose.tools.nontrivial import make_decorator
except ImportError:
    # It lives here in older versions of nose (el6)
    from nose.tools import make_decorator

import fedmsg.meta

from fedmsg.tests.common import load_config


def skip_on(attributes):
    """ A test decorator that will skip if any of the named attributes
    are left unspecified (are None-valued).
    """
    def wrapper(func):
        @make_decorator(func)
        def inner(self):
            for attr in attributes:
                if getattr(self, attr) is None:
                    raise SkipTest("%r left unspecified" % attr)
            return func(self)
        return inner
    return wrapper


def skip_if_fedmsg_meta_FI_is_present(f):
    """ A test decorator that will skip if fedmsg_meta_fedora_infrastructure
    is installed.

    The presence of that module will screw up some tests.
    """
    def _wrapper(self, *args, **kw):
        try:
            import fedmsg_meta_fedora_infrastructure
            raise SkipTest("fedmsg_meta_FI is present")
        except ImportError:
            pass

        return f(self, *args, **kw)

    return make_decorator(f)(_wrapper)


class TestForWarning(unittest.TestCase):
    def setUp(self):
        dirname = os.path.abspath(os.path.dirname(__file__))
        self.config = fedmsg.config.load_config(
            filenames=[os.path.join(dirname, "fedmsg-test-config.py")],
            invalidate_cache=True,
        )
        self.config['topic_prefix'] = 'org.fedoraproject'
        self.config['topic_prefix_re'] = '^org\.fedoraproject\.(dev|stg|prod)'

    @skip_if_fedmsg_meta_FI_is_present
    def test_for_no_plugins(self):
        """ Test that we print a warning if no plugin is installed """
        messages = []

        def mocked_warning(message):
            messages.append(message)

        expected = 'No fedmsg.meta plugins found.  fedmsg.meta.msg2* crippled'
        original = fedmsg.meta.log.warn
        try:
            fedmsg.meta.log.warn = mocked_warning
            fedmsg.meta.make_processors(**self.config)
            eq_(messages, [expected])
        finally:
            fedmsg.meta.log.warn = original


class TestProcessorRegex(unittest.TestCase):
    def setUp(self):
        dirname = os.path.abspath(os.path.dirname(__file__))
        self.config = fedmsg.config.load_config(
            filenames=[os.path.join(dirname, "fedmsg-test-config.py")],
            invalidate_cache=True,
        )
        self.config['topic_prefix'] = 'org.fedoraproject'
        self.config['topic_prefix_re'] = '^org\.fedoraproject\.(dev|stg|prod)'

        class MyGitProcessor(fedmsg.meta.base.BaseProcessor):
            __name__ = 'git'
            __description__ = 'This processor handles git messages'
            __link__ = 'http://fedmsg.com'
            __docs__ = 'http://fedmsg.com'
            __obj__ = 'git commits'

        self.proc = MyGitProcessor(lambda x: x, **self.config)

    def test_processor_handle_hit(self):
        """ Test that a proc can handle what it should. """
        fake_message = {
            'topic': 'org.fedoraproject.dev.git.push',
        }
        result = self.proc.handle_msg(fake_message, **self.config)
        assert result, "Proc didn't say it could handle the message."

    def test_processor_handle_miss(self):
        """ Test that a proc says it won't handle what it shouldn't. """
        fake_message = {
            'topic': 'org.fedoraproject.dev.github.push',
        }
        result = self.proc.handle_msg(fake_message, **self.config)
        assert not result, "Proc falsely claimed it could handle the msg."


class Base(unittest.TestCase):
    msg = None
    expected_title = None
    expected_subti = None
    expected_link = None
    expected_icon = None
    expected_secondary_icon = None
    expected_usernames = None
    expected_packages = None
    expected_objects = None
    expected_emails = None
    expected_avatars = None

    def setUp(self):
        dirname = os.path.abspath(os.path.dirname(__file__))
        self.config = fedmsg.config.load_config(
            filenames=[os.path.join(dirname, "fedmsg-test-config.py")],
            invalidate_cache=True,
        )
        self.config['topic_prefix'] = 'org.fedoraproject'
        self.config['topic_prefix_re'] = '^org\.fedoraproject\.(dev|stg|prod)'
        fedmsg.meta.make_processors(**self.config)

    @skip_on(['msg', 'expected_title'])
    def test_title(self):
        """ Does fedmsg.meta produce the expected title? """
        actual_title = fedmsg.meta.msg2title(self.msg, **self.config)
        eq_(actual_title, self.expected_title)

    @skip_on(['msg', 'expected_subti'])
    def test_subtitle(self):
        """ Does fedmsg.meta produce the expected subtitle? """
        actual_subti = fedmsg.meta.msg2subtitle(self.msg, **self.config)
        eq_(actual_subti, self.expected_subti)

    @skip_on(['msg', 'expected_link'])
    def test_link(self):
        """ Does fedmsg.meta produce the expected link? """
        actual_link = fedmsg.meta.msg2link(self.msg, **self.config)
        eq_(actual_link, self.expected_link)

    @skip_on(['msg', 'expected_icon'])
    def test_icon(self):
        """ Does fedmsg.meta produce the expected icon? """
        actual_icon = fedmsg.meta.msg2icon(self.msg, **self.config)
        eq_(actual_icon, self.expected_icon)

    @skip_on(['msg', 'expected_secondary_icon'])
    def test_secondary_icon(self):
        """ Does fedmsg.meta produce the expected secondary icon? """
        actual_icon = fedmsg.meta.msg2secondary_icon(self.msg, **self.config)
        eq_(actual_icon, self.expected_secondary_icon)

    @skip_on(['msg', 'expected_usernames'])
    def test_usernames(self):
        """ Does fedmsg.meta produce the expected list of usernames? """
        actual_usernames = fedmsg.meta.msg2usernames(self.msg, **self.config)
        eq_(actual_usernames, self.expected_usernames)

    @skip_on(['msg', 'expected_packages'])
    def test_packages(self):
        """ Does fedmsg.meta produce the expected list of packages? """
        actual_packages = fedmsg.meta.msg2packages(self.msg, **self.config)
        eq_(actual_packages, self.expected_packages)

    @skip_on(['msg', 'expected_objects'])
    def test_objects(self):
        """ Does fedmsg.meta produce the expected list of objects? """
        actual_objects = fedmsg.meta.msg2objects(self.msg, **self.config)
        eq_(actual_objects, self.expected_objects)

    @skip_on(['msg', 'expected_emails'])
    def test_emails(self):
        """ Does fedmsg.meta produce the expected list of emails? """
        actual_emails = fedmsg.meta.msg2emails(self.msg, **self.config)
        eq_(actual_emails, self.expected_emails)

    @skip_on(['msg', 'expected_avatars'])
    def test_avatars(self):
        """ Does fedmsg.meta produce the expected list of avatars? """
        actual_avatars = fedmsg.meta.msg2avatars(self.msg, **self.config)
        eq_(actual_avatars, self.expected_avatars)


class TestUnhandled(Base):
    expected_title = "unhandled_service.some_event"
    expected_subti = ""
    msg = {
        "topic": "org.fedoraproject.stg.unhandled_service.some_event"
    }


class TestAnnouncement(Base):
    expected_title = "announce.announcement"
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
    expected_title = "logger.log"
    expected_subti = 'hello, world. (ralph)'
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
    expected_title = "logger.log"
    expected_subti = '<custom JSON message> (root)'
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
