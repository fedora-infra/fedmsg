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
    msg, expected_title, expected_subti, expected_link = None, None, None, None

    def setUp(self):
        self.config = {
        }

    def test_title(self):
        """ Does fedmsg.text produce the expected title? """
        if None in (self.msg, self.expected_title):
            return
        actual_title = fedmsg.text._msg2title(self.msg, **self.config)
        eq_(actual_title, self.expected_title)

    def test_subtitle(self):
        """ Does fedmsg.text produce the expected subtitle? """
        if None in (self.msg, self.expected_subti):
            return
        actual_subti = fedmsg.text._msg2subtitle(self.msg, **self.config)
        eq_(actual_subti, self.expected_subti)

    def test_link(self):
        """ Does fedmsg.text produce the expected link? """
        if None in (self.msg, self.expected_link):
            return
        actual_link = fedmsg.text._msg2link(self.msg, **self.config)
        eq_(actual_link, self.expected_link)


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


class TestComposeBranchedComplete(Base):
    expected_title = "compose.branched.complete (unsigned)"
    expected_subti = "branched compose completed"
    expected_link = \
            "http://alt.fedoraproject.org/pub/fedora/linux/development"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.complete",
    }


class TestComposeBranchedStart(Base):
    expected_title = "compose.branched.start (unsigned)"
    expected_subti = "branched compose started"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.start",
    }


class TestComposeBranchedMashStart(Base):
    expected_title = "compose.branched.mash.start (unsigned)"
    expected_subti = "branched compose started mashing"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.mash.start",
    }


class TestComposeBranchedMashComplete(Base):
    expected_title = "compose.branched.mash.complete (unsigned)"
    expected_subti = "branched compose finished mashing"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.mash.complete",
    }


class TestComposeBranchedPungifyStart(Base):
    expected_title = "compose.branched.pungify.start (unsigned)"
    expected_subti = "started building boot.iso for branched"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.pungify.start",
    }


class TestComposeBranchedPungifyComplete(Base):
    expected_title = "compose.branched.pungify.complete (unsigned)"
    expected_subti = "finished building boot.iso for branched"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.pungify.complete",
    }


class TestComposeBranchedRsyncStart(Base):
    expected_title = "compose.branched.rsync.start (unsigned)"
    expected_subti = "started rsyncing branched compose for public consumption"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.rsync.start",
    }


class TestComposeBranchedRsyncComplete(Base):
    expected_title = "compose.branched.rsync.complete (unsigned)"
    expected_subti = \
            "finished rsync of branched compose for public consumption"
    expected_link = \
            "http://alt.fedoraproject.org/pub/fedora/linux/development"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.branched.rsync.complete",
    }


class TestComposeRawhideComplete(Base):
    expected_title = "compose.rawhide.complete (unsigned)"
    expected_subti = "rawhide compose completed"
    expected_link = \
            "http://alt.fedoraproject.org/pub/fedora/linux/development/rawhide"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.rawhide.complete",
    }


class TestComposeRawhideStart(Base):
    expected_title = "compose.rawhide.start (unsigned)"
    expected_subti = "rawhide compose started"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.rawhide.start",
    }


class TestComposeRawhideMashStart(Base):
    expected_title = "compose.rawhide.mash.start (unsigned)"
    expected_subti = "rawhide compose started mashing"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.rawhide.mash.start",
    }


class TestComposeRawhideMashComplete(Base):
    expected_title = "compose.rawhide.mash.complete (unsigned)"
    expected_subti = "rawhide compose finished mashing"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.rawhide.mash.complete",
    }


class TestComposeRawhideRsyncStart(Base):
    expected_title = "compose.rawhide.rsync.start (unsigned)"
    expected_subti = "started rsyncing rawhide compose for public consumption"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.rawhide.rsync.start",
    }


class TestComposeRawhideRsyncComplete(Base):
    expected_title = "compose.rawhide.rsync.complete (unsigned)"
    expected_subti = "finished rsync of rawhide compose for public consumption"
    expected_link = \
            "http://alt.fedoraproject.org/pub/fedora/linux/development/rawhide"
    msg = {
        "i": 1,
        "timestamp": 1344447839.891876,
        "topic": "org.fedoraproject.prod.compose.rawhide.rsync.complete",
    }


class TestBodhiUpdateComplete(Base):
    expected_title = "bodhi.update.complete.testing (unsigned)"
    expected_subti = "ralph's fedmsg-0.2.7-2.el6 bodhi update " + \
            "completed push to testing"
    expected_link = \
            "https://admin.fedoraproject.org/updates/fedmsg-0.2.7-2.el6"
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
    expected_link = "https://admin.fedoraproject.org/updates/foo"
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
    expected_link = "https://admin.fedoraproject.org/updates/foo"
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
    expected_link = "https://admin.fedoraproject.org/updates/foo"
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
    expected_link = "https://admin.fedoraproject.org/updates/foo"
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
    expected_link = "https://admin.fedoraproject.org/updates/foo"
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
    expected_subti = "ralph commented on bodhi update fedmsg-1.0-1 (karma: -1)"
    expected_link = "https://admin.fedoraproject.org/updates/fedmsg-1.0-1"
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


class TestBodhiOverrideUntagged(Base):
    expected_title = "bodhi.buildroot_override.untag (unsigned)"
    expected_subti = "lmacken expired a buildroot override for fedmsg-1.0-1"
    msg = {
        "i": 1,
        "timestamp": 1344964395.207541,
        "topic": "org.fedoraproject.stg.bodhi.buildroot_override.untag",
        "msg": {
            "override": {
                "build": "fedmsg-1.0-1",
                "submitter": "lmacken",
            }
        }
    }


class TestSupybotStartMeetingNoName(Base):
    expected_title = "meetbot.meeting.start (unsigned)"
    expected_subti = 'threebean started a meeting in #channel'
    msg = {
        "i": 16,
        "msg": {
            "meeting_topic": None,
            "attendees": {
                "fedmsg-test-bot": 2,
                "threebean": 2
            },
            "chairs": {},
            "url": "http://logs.com/awesome",
            "owner": "threebean",
            "channel": "#channel"
        },
        "topic": "org.fedoraproject.dev.meetbot.meeting.start",
        "timestamp": 1345572862.556145
    }


class TestSupybotStartMeeting(Base):
    expected_title = "meetbot.meeting.start (unsigned)"
    expected_subti = 'threebean started meeting "title" in #channel'
    msg = {
        "i": 16,
        "msg": {
            "meeting_topic": "title",
            "attendees": {
                "fedmsg-test-bot": 2,
                "threebean": 2
            },
            "chairs": {},
            "url": "http://logs.com/awesome",
            "owner": "threebean",
            "channel": "#channel"
        },
        "topic": "org.fedoraproject.dev.meetbot.meeting.start",
        "timestamp": 1345572862.556145
    }


class TestSupybotEndMeeting(Base):
    expected_title = "meetbot.meeting.complete (unsigned)"
    expected_subti = 'threebean ended meeting "title" in #channel'
    expected_link = 'http://logs.com/awesome.html'
    msg = {
        "i": 16,
        "msg": {
            "meeting_topic": "title",
            "attendees": {
                "fedmsg-test-bot": 2,
                "threebean": 2
            },
            "chairs": {},
            "url": "http://logs.com/awesome",
            "owner": "threebean",
            "channel": "#channel"
        },
        "topic": "org.fedoraproject.dev.meetbot.meeting.complete",
        "timestamp": 1345572862.556145
    }


class TestSupybotEndMeetingNoTitle(Base):
    expected_title = "meetbot.meeting.complete (unsigned)"
    expected_subti = 'threebean ended a meeting in #channel'
    expected_link = 'http://logs.com/awesome.html'
    msg = {
        "i": 16,
        "msg": {
            "meeting_topic": None,
            "attendees": {
                "fedmsg-test-bot": 2,
                "threebean": 2
            },
            "chairs": {},
            "url": "http://logs.com/awesome",
            "owner": "threebean",
            "channel": "#channel"
        },
        "topic": "org.fedoraproject.dev.meetbot.meeting.complete",
        "timestamp": 1345572862.556145
    }


class TestTaggerVoteAnonymous(Base):
    expected_title = "fedoratagger.tag.update (unsigned)"
    expected_subti = 'anonymous upvoted "unittest" on perl-Test-Fatal'
    expected_link = 'https://apps.fedoraproject.org/tagger/perl-Test-Fatal'
    msg = {
      "i": 1,
      "timestamp": 1345220838.2775879,
      "topic": "org.fedoraproject.stg.fedoratagger.tag.update",
      "msg": {
        "vote": {
          "tag": {
            "votes": 2,
            "like": 2,
            "package": {
              "perl-Test-Fatal": [
                {
                  "dislike": 0,
                  "total": 1,
                  "tag": "perl",
                  "votes": 1,
                  "like": 1
                },
                {
                  "dislike": 0,
                  "total": 2,
                  "tag": "unittest",
                  "votes": 2,
                  "like": 2
                }
              ]
            },
            "label": {
              "label": "unittest",
              "tags": [
                {
                  "dislike": 0,
                  "total": 2,
                  "tag": "unittest",
                  "votes": 2,
                  "like": 2
                }
              ]
            },
            "tag": "unittest",
            "dislike": 0,
            "total": 2
          },
          "like": True,
          "user": {
            "username": "anonymous",
            "all_votes": [],
            "votes": 0,
            "rank": -1
          }
        }
      }
    }


class TestTaggerCreate(Base):
    expected_title = "fedoratagger.tag.create (unsigned)"
    expected_subti = 'ralph added tag "unittest" to perl-Test-Fatal'
    expected_link = 'https://apps.fedoraproject.org/tagger/perl-Test-Fatal'
    msg = {
      "i": 1,
      "timestamp": 1345220073.4948981,
      "topic": "org.fedoraproject.stg.fedoratagger.tag.create",
      "msg": {
        "vote": {
          "tag": {
            "votes": 1,
            "like": 1,
            "package": {
              "perl-Test-Fatal": [
                {
                  "dislike": 0,
                  "total": 1,
                  "tag": "unittest",
                  "votes": 1,
                  "like": 1
                },
                {
                  "dislike": 0,
                  "total": 1,
                  "tag": "perl",
                  "votes": 1,
                  "like": 1
                }
              ]
            },
            "label": {
              "label": "unittest",
              "tags": [
                {
                  "dislike": 0,
                  "total": 1,
                  "tag": "unittest",
                  "votes": 1,
                  "like": 1
                }
              ]
            },
            "tag": "unittest",
            "dislike": 0,
            "total": 1
          },
          "like": True,
          "user": {
            "username": "ralph",
            "votes": 28,
            "rank": 1
          }
        }
      }
    }


class TestMediaWikiEdit(Base):
    expected_title = "wiki.article.edit (unsigned)"
    expected_subti = 'Ralph made a wiki edit to "Messaging SIG".'
    expected_link = "http://this-is-a-link.org"

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


class TestPkgdb2BrMassStart(Base):
    expected_title = "git.mass_branch.start (unsigned)"
    expected_subti = "dgilmore started a mass branch"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.mass_branch.start",
        "msg": {
            "agent": "dgilmore",
        },
    }


class TestPkgdb2BrMassComplete(Base):
    expected_title = "git.mass_branch.complete (unsigned)"
    expected_subti = "mass branch started by dgilmore completed"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.mass_branch.complete",
        "msg": {
            "agent": "dgilmore",
        },
    }


class TestPkgdb2BrRunStart(Base):
    expected_title = "git.pkgdb2branch.start (unsigned)"
    expected_subti = "limburgher started a run of pkgdb2branch"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.pkgdb2branch.start",
        "msg": {
            "agent": "limburgher",
        },
    }


class TestPkgdb2BrRunComplete(Base):
    expected_title = "git.pkgdb2branch.complete (unsigned)"
    expected_subti = "run of pkgdb2branch started by limburgher completed"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.pkgdb2branch.complete",
        "msg": {
            "agent": "limburgher",
            "unbranchedPackages": [],
        },
    }


class TestPkgdb2BrRunCompleteWithError(Base):
    expected_title = "git.pkgdb2branch.complete (unsigned)"
    expected_subti = "run of pkgdb2branch started by limburgher completed" + \
            " with 1 error"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.pkgdb2branch.complete",
        "msg": {
            "agent": "limburgher",
            "unbranchedPackages": ['foo'],
        },
    }


class TestPkgdb2BrRunCompleteWithErrors(Base):
    expected_title = "git.pkgdb2branch.complete (unsigned)"
    expected_subti = "run of pkgdb2branch started by limburgher completed" + \
            " with 2 errors"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.pkgdb2branch.complete",
        "msg": {
            "agent": "limburgher",
            "unbranchedPackages": ['foo', 'bar'],
        },
    }


class TestPkgdb2BrCreate(Base):
    expected_title = "git.branch.valgrind.master (unsigned)"
    expected_subti = \
       "limburgher created branch 'master' for the 'valgrind' package"
    expected_link = \
       "http://pkgs.fedoraproject.org/cgit/valgrind.git/log/?h=master"
    msg = {
        "i": 1,
        "timestamp": 1344350850.8867381,
        "topic": "org.fedoraproject.prod.git.branch.valgrind.master",
        "msg": {
            "agent": "limburgher",
        },
    }


class TestSCM(Base):
    expected_title = "git.receive.valgrind.master (unsigned)"
    expected_subti = 'Mark Wielaard pushed to valgrind (master).  ' + \
            '"Clear CFLAGS CXXFLAGS LDFLAGS."'
    expected_link = "http://pkgs.fedoraproject.org/cgit/" + \
            "valgrind.git/commit/" + \
            "?h=master&id=7a98f80d9b61ce167e4ef8129c81ed9284ecf4e1"
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
