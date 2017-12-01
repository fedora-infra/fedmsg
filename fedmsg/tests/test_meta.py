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

import inspect
import functools
import os
import textwrap
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import fedmsg.meta


class UnspecifiedType(object):
    """ A sentinel used to identify which expectations are not specified. """
    def __str__(self):
        return "Unspecified"

    def __unicode__(self):
        return u"Unspecified"

    def __repr__(self):
        return "Unspecified"


Unspecified = UnspecifiedType()


def skip_on(attributes):
    """ A test decorator that will skip if any of the named attributes
    are left unspecified.
    """
    def wrapper(func):
        @functools.wraps(func)
        def inner(self):
            for attr in attributes:
                if getattr(self, attr) is Unspecified:
                    raise unittest.SkipTest("%r left unspecified" % attr)
            return func(self)
        return inner
    return wrapper


try:
    import fedmsg_meta_fedora_infrastructure  # noqa: F401
    _fedmsg_meta_fi = True
except ImportError:
    _fedmsg_meta_fi = False


skip_if_fedmsg_meta_FI_is_present = unittest.skipIf(_fedmsg_meta_fi, "fedmsg_meta_FI is present")


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
            fedmsg.meta.processors = []
            fedmsg.meta.log.warn = mocked_warning
            fedmsg.meta.make_processors(**self.config)
            self.assertEqual(messages, [expected])
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
        assert result is not None, "Proc didn't say it could handle the message."

    def test_processor_handle_miss(self):
        """ Test that a proc says it won't handle what it shouldn't. """
        fake_message = {
            'topic': 'org.fedoraproject.dev.github.push',
        }
        result = self.proc.handle_msg(fake_message, **self.config)
        assert result is None, "Proc falsely claimed it could handle the msg."

    def test_processor_handle_empty_subtopic(self):
        """Test that a processor will handle a message with an empty subtopic"""
        fake_message = {
            'topic': 'org.fedoraproject.dev.git',
        }
        result = self.proc.handle_msg(fake_message, **self.config)
        assert result is "", "Proc said it couldn't handle the msg."


class Base(unittest.TestCase):
    msg = Unspecified
    expected_title = Unspecified
    expected_subti = Unspecified
    expected_subjective = Unspecified
    expected_link = Unspecified
    expected_icon = Unspecified
    expected_secondary_icon = Unspecified
    expected_usernames = Unspecified
    expected_agent = Unspecified
    expected_packages = Unspecified
    expected_objects = Unspecified
    expected_emails = Unspecified
    expected_avatars = Unspecified
    expected_long_form = Unspecified

    def setUp(self):
        dirname = os.path.abspath(os.path.dirname(__file__))
        self.config = fedmsg.config.load_config(
            filenames=[os.path.join(dirname, "fedmsg-test-config.py")],
            invalidate_cache=True,
        )
        self.config['topic_prefix'] = 'org.fedoraproject'
        self.config['topic_prefix_re'] = '^org\.fedoraproject\.(dev|stg|prod)'
        fedmsg.meta.make_processors(**self.config)

        self.maxDiff = None
        # Support fancy unittest py2.7 interface on older pythons
        if not hasattr(self, 'assertMultiLineEqual'):
            self.assertMultiLineEqual = self.assertEqual

    def _equals(self, actual, expected, multiline=False):
        try:
            if multiline:
                self.assertMultiLineEqual(actual, expected)
            else:
                self.assertEquals(actual, expected)
        except:  # noqa: E722
            print("Failed at:")
            print(" ", self)
            print(" ", os.path.relpath(inspect.getfile(type(self))[:-1]))
            raise

    @skip_on(['msg', 'expected_title'])
    def test_title(self):
        """ Does fedmsg.meta produce the expected title? """
        actual_title = fedmsg.meta.msg2title(self.msg, **self.config)
        self._equals(actual_title, self.expected_title)

    @skip_on(['msg', 'expected_long_form'])
    def test_long_form(self):
        """ Does fedmsg.meta produce the expected long form text? """
        actual_long_form = fedmsg.meta.msg2long_form(self.msg, **self.config)
        self._equals(actual_long_form, self.expected_long_form, multiline=True)

    @skip_on(['msg', 'expected_subti'])
    def test_subtitle(self):
        """ Does fedmsg.meta produce the expected subtitle? """
        actual_subti = fedmsg.meta.msg2subtitle(self.msg, **self.config)
        self._equals(actual_subti, self.expected_subti)

    @skip_on(['msg', 'expected_subjective'])
    def test_subjective(self):
        """ Does fedmsg.meta produce the expected subjective message? """
        for subject, expected in self.expected_subjective.items():
            actual_subjective = fedmsg.meta.msg2subjective(
                self.msg, subject=subject, **self.config)
            self._equals(actual_subjective, expected)

    @skip_on(['msg', 'expected_link'])
    def test_link(self):
        """ Does fedmsg.meta produce the expected link? """
        actual_link = fedmsg.meta.msg2link(self.msg, **self.config)
        self._equals(actual_link, self.expected_link)

    @skip_on(['msg', 'expected_icon'])
    def test_icon(self):
        """ Does fedmsg.meta produce the expected icon? """
        actual_icon = fedmsg.meta.msg2icon(self.msg, **self.config)
        self._equals(actual_icon, self.expected_icon)

    @skip_on(['msg', 'expected_secondary_icon'])
    def test_secondary_icon(self):
        """ Does fedmsg.meta produce the expected secondary icon? """
        actual_icon = fedmsg.meta.msg2secondary_icon(self.msg, **self.config)
        self._equals(actual_icon, self.expected_secondary_icon)

    @skip_on(['msg', 'expected_usernames'])
    def test_usernames(self):
        """ Does fedmsg.meta produce the expected list of usernames? """
        actual_usernames = fedmsg.meta.msg2usernames(self.msg, **self.config)
        self._equals(actual_usernames, self.expected_usernames)

    @skip_on(['msg', 'expected_agent'])
    def test_agent(self):
        """ Does fedmsg.meta produce the expected agent? """
        actual_agent = fedmsg.meta.msg2agent(self.msg, **self.config)
        self._equals(actual_agent, self.expected_agent)

    @skip_on(['msg', 'expected_packages'])
    def test_packages(self):
        """ Does fedmsg.meta produce the expected list of packages? """
        actual_packages = fedmsg.meta.msg2packages(self.msg, **self.config)
        self._equals(actual_packages, self.expected_packages)

    @skip_on(['msg', 'expected_objects'])
    def test_objects(self):
        """ Does fedmsg.meta produce the expected list of objects? """
        actual_objects = fedmsg.meta.msg2objects(self.msg, **self.config)
        self._equals(actual_objects, self.expected_objects)

    @skip_on(['msg', 'expected_emails'])
    def test_emails(self):
        """ Does fedmsg.meta produce the expected list of emails? """
        actual_emails = fedmsg.meta.msg2emails(self.msg, **self.config)
        self._equals(actual_emails, self.expected_emails)

    @skip_on(['msg', 'expected_avatars'])
    def test_avatars(self):
        """ Does fedmsg.meta produce the expected list of avatars? """
        actual_avatars = fedmsg.meta.msg2avatars(self.msg, **self.config)
        self._equals(actual_avatars, self.expected_avatars)


class TestUnhandled(Base):
    expected_agent = None
    expected_avatars = {}
    expected_emails = {}
    expected_icon = None
    expected_link = ''
    expected_long_form = ''
    expected_objects = set()
    expected_packages = set()
    expected_secondary_icon = None
    expected_subti = ""
    expected_title = "unhandled_service.some_event"
    expected_usernames = set()

    expected_subjective = {
        'foo': expected_subti,
        'bar': expected_subti,
    }

    msg = {
        "topic": "org.fedoraproject.stg.unhandled_service.some_event"
    }


class TestAnnouncement(Base):
    expected_agent = 'ralph'
    expected_avatars = {}
    expected_emails = {}
    expected_icon = None
    expected_link = 'foo'
    expected_long_form = 'hello, world.'
    expected_objects = set()
    expected_packages = set()
    expected_secondary_icon = None
    expected_subti = 'hello, world.'
    expected_title = "announce.announcement"
    expected_usernames = set(['ralph'])

    expected_subjective = {
        'foo': expected_subti,
        'bar': expected_subti,
    }

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
    expected_agent = 'ralph'
    expected_avatars = {}
    expected_emails = {}
    expected_icon = None
    expected_link = ''
    expected_long_form = 'hello, world. (ralph)'
    expected_objects = set()
    expected_packages = set()
    expected_secondary_icon = None
    expected_subti = 'hello, world. (ralph)'
    expected_title = "logger.log"
    expected_usernames = set(['ralph'])

    expected_subjective = {
        'ralph': 'you logged "hello, world."',
        'lmacken': expected_subti,
    }

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
    expected_agent = 'root'
    expected_avatars = {}
    expected_emails = {}
    expected_icon = None
    expected_link = ''
    expected_objects = set()
    expected_packages = set()
    expected_secondary_icon = None
    expected_subti = '<custom JSON message> (root)'
    expected_title = "logger.log"
    expected_usernames = set(['root'])

    expected_long_form = textwrap.dedent("""
    A custom JSON message was logged by root::

        "msg": {
            "foo": "bar"
        }
    """).strip()

    expected_subjective = {
        'foo': expected_subti,
        'bar': expected_subti,
    }

    msg = {
        "i": 1,
        "timestamp": 1344352929.415939,
        "topic": "org.fedoraproject.dev.logger.log",
        "msg": {
            "foo": "bar"
        },
        'username': 'root',
    }


class ConglomerateBase(unittest.TestCase):
    originals = Unspecified
    expected = Unspecified
    maxDiff = None

    def setUp(self):
        dirname = os.path.abspath(os.path.dirname(__file__))
        self.config = fedmsg.config.load_config(
            filenames=[os.path.join(dirname, "fedmsg-test-config.py")],
            invalidate_cache=True,
        )
        self.config['topic_prefix'] = 'org.fedoraproject'
        self.config['topic_prefix_re'] = '^org\.fedoraproject\.(dev|stg|prod)'
        fedmsg.meta.make_processors(**self.config)

        # Delete the msg_ids field because it is bulky and I don't want to
        # bother with testing it (copying and pasting it).
        if self.expected is not Unspecified:
            for item in self.expected:
                if 'msg_ids' in item:
                    del item['msg_ids']

    @skip_on(['originals', 'expected'])
    def test_conglomerate(self):
        """ Does fedmsg.meta produce the expected conglomeration? """
        subject = getattr(self, 'subject', None)
        actual = fedmsg.meta.conglomerate(
            self.originals, subject, **self.config)

        # Delete the msg_ids field because it is bulky and I don't want to
        # bother with testing it (copying and pasting it).
        if actual:
            for item in actual:
                if 'msg_ids' in item:
                    del item['msg_ids']

        try:
            self.assertEquals(actual, self.expected)
        except:  # noqa: E722
            print("Failed at:")
            print(" ", self)
            print(" ", os.path.relpath(inspect.getfile(type(self))[:-1]))
            raise


class TestConglomeratorExtras(unittest.TestCase):
    def setUp(self):
        dirname = os.path.abspath(os.path.dirname(__file__))
        self.config = fedmsg.config.load_config(
            filenames=[os.path.join(dirname, "fedmsg-test-config.py")],
            invalidate_cache=True,
        )
        self.config['topic_prefix'] = 'org.fedoraproject'
        self.config['topic_prefix_re'] = '^org\.fedoraproject\.(dev|stg|prod)'

        self.conglomerator = fedmsg.meta.base.BaseConglomerator

    def test_list_to_series_simple(self):
        original, expected = ['a', 'b', 'c'], "a, b, and c"
        result = self.conglomerator.list_to_series(original)
        self.assertEqual(result, expected)

    def test_list_to_series_single_duplicate(self):
        original, expected = ['a', 'a', 'a'], "a"
        result = self.conglomerator.list_to_series(original)
        self.assertEqual(result, expected)

    def test_list_to_series_double_duplicate(self):
        original, expected = ['a', 'a', 'b', 'b'], "a and b"
        result = self.conglomerator.list_to_series(original)
        self.assertEqual(result, expected)

    def test_list_to_series_backheavy_duplicate(self):
        original, expected = ['a', 'b', 'b', 'b'], "a and b"
        result = self.conglomerator.list_to_series(original)
        self.assertEqual(result, expected)


class TestMetaExtras(unittest.TestCase):
    def test_graceful_keyerror(self):
        """ Ensure that the graceful decorator handles KeyErrors """

        expected = "default value"

        @fedmsg.meta.graceful(lambda: expected)
        def f(msg, **config):
            raise KeyError("Who changed the API!?")

        actual = f({})
        self.assertEquals(actual, expected)

    def test_graceful_other_error(self):
        """ Ensure that the graceful decorator doesn't handle non-KeyErrors """

        @fedmsg.meta.graceful(lambda: "default value")
        def f(msg, **config):
            raise Exception("This is worse than we thought.")

        with self.assertRaises(Exception):
            f({})


if __name__ == '__main__':
    unittest.main()
