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


class TestFASUserCreate(Base):
    expected_title = "fas.user.create (unsigned)"
    expected_subti = "New FAS account:  'ralph'  (created by 'ralph')"
    msg = {
        u'i': 1,
        u'timestamp': 1344432054.8098609,
        u'topic': u'org.fedoraproject.stg.fas.user.create',
        u'msg': {
            u'user': {
                u'username': u'ralph'
            },
            u'agent': {
                u'username': u'ralph'
            }
        }
    }


class TestFASEditProfile(Base):
    expected_title = "fas.user.update (unsigned)"
    expected_subti = "ralph edited the following fields of ralph's " + \
            "FAS profile:  comments"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.user.update',
        u'msg': {
            u'fields': [u'comments'],
            u'user': {u'username': u'ralph'},
            u'agent': {u'username': u'ralph'},
        }
    }


class TestFASEditGroup(Base):
    expected_title = "fas.group.update (unsigned)"
    expected_subti = "ralph edited the following fields of the " + \
            "ambassadors FAS group:  display_name"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.group.update',
        u'msg': {
            u'fields': [u'display_name'],
            u'group': {u'name': u'ambassadors'},
            u'agent': {u'username': u'ralph'},
        }
    }


class TestFASGroupCreate(Base):
    expected_title = "fas.group.create (unsigned)"
    expected_subti = "ralph created new FAS group ambassadors"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.group.create',
        u'msg': {
            u'group': {u'name': u'ambassadors'},
            u'agent': {u'username': u'ralph'},
        }
    }


class TestFASRoleUpdate(Base):
    expected_title = "fas.role.update (unsigned)"
    expected_subti = "toshio changed ralph's role in the ambassadors group"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.role.update',
        u'msg': {
            u'group': {u'name': u'ambassadors'},
            u'user': {u'username': u'ralph'},
            u'agent': {u'username': u'toshio'},
        }
    }


class TestFASGroupRemove(Base):
    expected_title = "fas.group.member.remove (unsigned)"
    expected_subti = "toshio removed ralph from " + \
            "the ambassadors group"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.group.member.remove',
        u'msg': {
            u'group': {u'name': u'ambassadors'},
            u'user': {u'username': u'ralph'},
            u'agent': {u'username': u'toshio'},
        }
    }


class TestFASGroupSponsor(Base):
    expected_title = "fas.group.member.sponsor (unsigned)"
    expected_subti = "toshio sponsored ralph's membership " + \
            "in the ambassadors group"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.group.member.sponsor',
        u'msg': {
            u'group': {u'name': u'ambassadors'},
            u'user': {u'username': u'ralph'},
            u'agent': {u'username': u'toshio'},
        }
    }


class TestFASGroupApply(Base):
    expected_title = "fas.group.member.apply (unsigned)"
    expected_subti = "ralph applied for ralph's membership " + \
            "in the ambassadors group"
    msg = {
        u'topic': u'org.fedoraproject.stg.fas.group.member.apply',
        u'msg': {
            u'group': {u'name': u'ambassadors'},
            u'user': {u'username': u'ralph'},
            u'agent': {u'username': u'ralph'},
        }
    }


class TestBodhiUpdateComplete(Base):
    expected_title = "bodhi.update.complete.testing (unsigned)"
    expected_subti = "ralph's fedmsg-0.2.7-2.el6 bodhi update " + \
            "completed push to testing"
    msg = {
        "i": 88,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.bodhi.update.complete.testing",
        "msg": {
            "update": {
                "close_bugs": True,
                "critpath": False,
                "stable_karma": 3,
                "date_pushed": 1344447839.0,
                "title": "fedmsg-0.2.7-2.el6",
                "nagged": None,
                "comments": [
                    {
                        "group": None,
                        "author": "bodhi",
                        "text": "This update has been submitted for " + \
                                "testing by ralph. ",
                        "karma": 0,
                        "anonymous": False,
                        "timestamp": 1344266157.0
                    },
                    {
                        "group": None,
                        "author": "bodhi",
                        "text": "This update is currently being pushed " + \
                                "to the Fedora EPEL 6 testing updates " + \
                                "repository.",
                        "karma": 0,
                        "anonymous": False,
                        "timestamp": 1344443927.0
                    }
                ],
                "updateid": "FEDORA-EPEL-2012-6650",
                "type": "bugfix",
                "status": "testing",
                "date_submitted": 1344266152.0,
                "unstable_karma": -3,
                "release": {
                    "dist_tag": "dist-6E-epel",
                    "id_prefix": "FEDORA-EPEL",
                    "locked": False,
                    "name": "EL-6",
                    "long_name": "Fedora EPEL 6"
                },
                "approved": None,
                "builds": [
                    {
                        "nvr": "fedmsg-0.2.7-2.el6",
                        "package": {
                            "suggest_reboot": False,
                            "committers": [
                                "ralph"
                            ],
                            "name": "fedmsg"
                        }
                    }
                ],
                "date_modified": None,
                "notes": "Bugfix - Added a forgotten new " + \
                        "requirement on python-requests.",
                "request": None,
                "bugs": [],
                "critpath_approved": False,
                "karma": 0,
                "submitter": "ralph",
            }
        }
    }


class TestBodhiMashTaskMashing(Base):
    expected_title = "bodhi.mashtask.mashing (unsigned)"
    expected_subti = "bodhi masher is mashing test_repo"
    msg = {
        'topic': "org.fedoraproject.prod.bodhi.mashtask.mashing",
        'msg': {
            'repo': 'test_repo',
        },
    }


class TestBodhiMashTaskStart(Base):
    expected_title = "bodhi.mashtask.start (unsigned)"
    expected_subti = "bodhi masher started its mashtask"
    msg = {
        'topic': "org.fedoraproject.prod.bodhi.mashtask.start",
        'msg': {}
    }


class TestBodhiMashTaskComplete(Base):
    expected_title = "bodhi.mashtask.complete (unsigned)"
    expected_subti = "bodhi masher failed to complete its mashtask!"
    msg = {
        'topic': "org.fedoraproject.prod.bodhi.mashtask.complete",
        'msg': {'success': False}
    }


class TestBodhiMashTaskSyncWait(Base):
    expected_title = "bodhi.mashtask.sync.wait (unsigned)"
    expected_subti = "bodhi masher is waiting on mirror repos to sync"
    msg = {
        'topic': "org.fedoraproject.prod.bodhi.mashtask.sync.wait",
        'msg': {}
    }


class TestBodhiMashTaskSyncWait(Base):
    expected_title = "bodhi.mashtask.sync.done (unsigned)"
    expected_subti = "bodhi masher finished waiting on mirror repos to sync"
    msg = {
        'topic': "org.fedoraproject.prod.bodhi.mashtask.sync.done",
        'msg': {}
    }


class TestBodhiRequestUnpush(Base):
    expected_title = "bodhi.update.request.unpush (unsigned)"
    expected_subti = "lmacken unpushed foo"
    msg = {
        'topic': "org.fedoraproject.dev.bodhi.update.request.unpush",
        'msg': {
            'update': {
                'title': 'foo',
                'submitter': 'lmacken',
            },
        },
    }


class TestBodhiRequestObsolete(Base):
    expected_title = "bodhi.update.request.obsolete (unsigned)"
    expected_subti = "lmacken obsoleted foo"
    msg = {
        'topic': "org.fedoraproject.dev.bodhi.update.request.obsolete",
        'msg': {
            'update': {
                'title': 'foo',
                'submitter': 'lmacken',
            },
        },
    }


class TestBodhiRequestStable(Base):
    expected_title = "bodhi.update.request.stable (unsigned)"
    expected_subti = "lmacken submitted foo to stable"
    msg = {
        'topic': "org.fedoraproject.dev.bodhi.update.request.stable",
        'msg': {
            'update': {
                'title': 'foo',
                'submitter': 'lmacken',
            },
        },
    }


class TestBodhiRequestRevoke(Base):
    expected_title = "bodhi.update.request.revoke (unsigned)"
    expected_subti = "lmacken revoked foo"
    msg = {
        'topic': "org.fedoraproject.dev.bodhi.update.request.revoke",
        'msg': {
            'update': {
                'title': 'foo',
                'submitter': 'lmacken',
            },
        },
    }


class TestBodhiRequestTesting(Base):
    expected_title = "bodhi.update.request.testing (unsigned)"
    expected_subti = "lmacken submitted foo to testing"
    msg = {
        'topic': "org.fedoraproject.dev.bodhi.update.request.testing",
        'msg': {
            'update': {
                'title': 'foo',
                'submitter': 'lmacken',
            },
        },
    }


class TestBodhiComment(Base):
    expected_title = "bodhi.update.comment (unsigned)"
    expected_subti = "ralph commented on a bodhi update " + \
            "fedmsg-1.0-1 (karma: -1)"
    msg = {
        "i": 1,
        "timestamp": 1344344053.2337201,
        "topic": "org.fedoraproject.stg.bodhi.update.comment",
        "msg": {
            "comment": {
                "update_title": "fedmsg-1.0-1",
                "group": None,
                "author": "ralph",
                "text": "Can you believe how much testing we're doing?",
                "karma": -1,
                "anonymous": False,
                "timestamp": 1344344050.0
            }
        }
    }


class TestBodhiOverrideTagged(Base):
    expected_title = "bodhi.buildroot_override.tag (unsigned)"
    expected_subti = "lmacken submitted a buildroot override for fedmsg-1.0-1"
    msg = {
        "i": 1,
        "timestamp": 1344344053.2337201,
        "topic": "org.fedoraproject.stg.bodhi.buildroot_override.tag",
        "msg": {
            "override": {
                "build": "fedmsg-1.0-1",
                "submitter": "lmacken",
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


class TestTaggerCreate(Base):
    expected_title = "fedoratagger.tag.create (unsigned)"
    expected_subti = 'Added new tag "awesome"'
    msg = {
        "i": 2,
        "timestamp": 1344360737.9752989,
        "topic": "org.fedoraproject.stg.fedoratagger.tag.create",
        "msg": {
            "tag": {
                "dislike": 0,
                "total": 1,
                "tag": "awesome",
                "votes": 1,
                "like": 1
            }
        }
    }


class TestTaggerLogin(Base):
    expected_title = "fedoratagger.login.tagger (unsigned)"
    expected_subti = "ralph logged in to fedoratagger"
    msg = {
        "i": 2,
        "timestamp": 1344360950.296824,
        "topic": "org.fedoraproject.stg.fedoratagger.login.tagger",
        "msg": {
            "user": {
                "username": "ralph",
                "votes": 26,
                "rank": 1
            }
        }
    }


class TestMediaWikiEdit(Base):
    expected_title = "wiki.article.edit (unsigned)"
    expected_subti = 'Ralph made a wiki edit to "Messaging SIG".  ' + \
            'http://this-is-a-link.org'
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
            "revision": None,
            "url": "http://this-is-a-link.org"
        },
        "timestamp": 1344350200
    }


class TestMediaWikiUpload(Base):
    expected_title = "wiki.upload.complete (unsigned)"
    expected_subti = 'Ralph uploaded File:Cat.jpg to the wiki: ' + \
            '"This is a beautiful cat..."'
    msg = {
        "topic": "org.fedoraproject.stg.wiki.upload.complete",
        "msg": {
            "user_id": 8306,
            "description": "This is a beautiful cat",
            "title": {
                "mCascadeSources": [],
                "mLength": -1,
                "mInterwiki": "",
                "mNotificationTimestamp": [],
                "mCascadeRestriction": None,
                "mRedirect": None,
                "mArticleID": 46586,
                "mTextform": "Cat.jpg",
                "mWatched": None,
                "mDbkeyform": "Cat.jpg",
                "mCascadingRestrictions": [],
                "mDefaultNamespace": 0,
                "mRestrictions": [],
                "mUrlform": "Cat.jpg",
                "mLatestID": False,
                "mBacklinkCache": {},
                "mNamespace": 6,
                "mUserCaseDBKey": "Cat.jpg",
                "mTitleProtection": False,
                "mOldRestrictions": False,
                "mFragment": "",
                "mHasCascadingRestrictions": None,
                "mPrefixedText": "File:Cat.jpg",
                "mRestrictionsExpiry": {
                    "create": "infinity"
                },
                "mRestrictionsLoaded": False
            },
            "user_text": "Ralph",
            "minor_mime": "jpeg",
            "url": "/w/uploads/d/d1/Cat.jpg",
            "file_exists": True,
            "mime": "image/jpeg",
            "major_mime": "image",
            "media_type": "BITMAP",
            "size": 295667
        },
        "timestamp": 1344361406
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
    expected_title = "git.receive.valgrind.master (unsigned)"
    expected_subti = 'Mark Wielaard pushed to valgrind (master).  ' + \
            '"Clear CFLAGS CXXFLAGS LDFLAGS."'
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.receive.valgrind.master",
        "msg": {
            "commit": {
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
                "message": """Clear CFLAGS CXXFLAGS LDFLAGS.
                This is a bit of a hammer.""",
                "email": "mjw@redhat.com",
                "branch": "master",
            }
        }
    }


if __name__ == '__main__':
    unittest.main()
