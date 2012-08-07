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


if __name__ == '__main__':
    unittest.main()
