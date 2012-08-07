""" Tests for fedmsg.text """

import unittest
from nose.tools import eq_

import fedmsg.text


class Base(unittest.TestCase):
    msg, expected_title, expected_subti = None, None, None

    def setUp(self):
        self.config = {
        }

    def test_title(self):
        """ Does fedmsg.text produce the expected title? """
        if None in (self.msg, self.expected_title, self.expected_subti):
            return
        actual_title = fedmsg.text._msg2title(self.msg, **self.config)
        eq_(actual_title, self.expected_title)

    def test_subtitle(self):
        """ Does fedmsg.text produce the expected subtitle? """
        if None in (self.msg, self.expected_title, self.expected_subti):
            return
        actual_subti = fedmsg.text._msg2subtitle(self.msg, **self.config)
        eq_(actual_subti, self.expected_subti)


class TestUnhandled(Base):
    expected_title = "unhandled_service.some_event (unsigned)"
    expected_subti = ""
    msg = {
        "topic": "org.fedoraproject.stg.unhandled_service.some_event"
    }


class TestBodhiComment(Base):
    expected_title = "bodhi.update.comment (unsigned)"
    expected_subti = "ralph commented on a bodhi update (karma: -1)"
    msg = {
        "i": 1,
        "timestamp": 1344344053.2337201,
        "topic": "org.fedoraproject.stg.bodhi.update.comment",
        "msg": {
            "comment": {
                "group": None,
                "author": "ralph",
                "text": "Can you believe how much testing we're doing?",
                "karma": -1,
                "anonymous": False,
                "timestamp": 1344344050.0
            }
        }
    }


class TestTaggerVoteAnonymous(Base):
    expected_title = "fedoratagger.tag.update (unsigned)"
    expected_subti = "anonymous voted on the package tag 'foo'"
    msg = {
        "i": 1,
        "timestamp": 1344344522.1364241,
        "topic": "org.fedoraproject.stg.fedoratagger.tag.update",
        "msg": {
            "tag": {
                "dislike": 1,
                "total": 3,
                "tag": "foo",
                "votes": 5,
                "like": 4
            },
            "user": {
                "username": "anonymous",
                "votes": 0,
                "rank": -1
            }
        }
    }


class TestMediaWikiEdit(Base):
    expected_title = "wiki.article.edit (unsigned)"
    expected_subti = 'Ralph made a wiki edit to "Messaging SIG"'
    msg = {
        "topic": "org.fedoraproject.stg.wiki.article.edit",
        "msg": {
            "watch_this": None,
            "base_rev_id": False,
            "title": "Messaging SIG",
            "minor_edit": 0,
            "text": "The diff goes here...",
            "section_anchor": None,
            "summary": "/* Mission */ ",
            "user": "Ralph",
            "revision": None
        },
        "timestamp": 1344350200
    }


class TestLoggerNormal(Base):
    expected_title = "logger.log (unsigned)"
    expected_subti = 'hello, world.'
    msg = {
        "i": 1,
        "timestamp": 1344352873.714926,
        "topic": "org.fedoraproject.dev.logger.log",
        "msg": {
            "log": "hello, world."
        }
    }

class TestLoggerJSON(Base):
    expected_title = "logger.log (unsigned)"
    expected_subti = '<custom JSON message>'
    msg = {
        "i": 1,
        "timestamp": 1344352929.415939,
        "topic": "org.fedoraproject.dev.logger.log",
        "msg": {
            "foo": "bar"
        }
    }



class TestSCM(Base):
    expected_title = "git.valgrind.git.receive (unsigned)"
    expected_subti = 'Mark Wielaard pushed to valgrind.git.  ' + \
            '"Clear CFLAGS CXXFLAGS LDFLAGS."'
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.valgrind.git.receive",
        "msg": {
            "commits": [
                {
                    "stats": {
                        "files": {
                            "valgrind.spec": {
                                "deletions": 2,
                                "lines": 3,
                                "insertions": 1
                            }
                        },
                        "total": {
                            "deletions": 2,
                            "files": 1,
                            "insertions": 1,
                            "lines": 3
                        }
                    },
                    "name": "Mark Wielaard",
                    "rev": "7a98f80d9b61ce167e4ef8129c81ed9284ecf4e1",
                    "summary": "Clear CFLAGS CXXFLAGS LDFLAGS.",
                    "message": "Clear CFLAGS CXXFLAGS LDFLAGS.\n\nThis is a bit of a hammer, but without this the regtests results are just\nhorrible with hundreds of failures. Even with this there are 29 failures.\nOnce we fix those and have a clean testsuite we should reinstate the\nFLAGS and figure out exactly which ones cause the massive fails.\n",
                    "email": "mjw@redhat.com"
                }
            ]
        }
    }


if __name__ == '__main__':
    unittest.main()
