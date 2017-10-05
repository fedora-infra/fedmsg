# This file is part of fedmsg.
# Copyright (C) 2013 Simon Chopin <chopin.simon@gmail.com
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
# Authors: Simon Chopin <chopin.simon@gmail.com>
#
''' Tests for fedmsg.replay '''

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock
import json
from datetime import datetime
import zmq
import socket
from threading import Thread, Event

from fedmsg.tests.common import load_config, requires_network

from fedmsg.replay import ReplayContext, get_replay

from fedmsg.replay.sqlstore import SqlStore, SqlMessage
from sqlalchemy import create_engine

hostname = socket.gethostname().split('.', 1)[0]
local_name = '{0}.{1}'.format(unittest.__name__, hostname)


class ReplayContextTests(unittest.TestCase):

    def test_init_missing_endpoint(self):
        """ Try to initialize the context with a nonexistant service name. """
        with self.assertRaises(KeyError):
            config = load_config()
            config['persistent_store'] = mock.Mock()
            config['name'] = "failboat"
            ReplayContext(**config)

    def test_init_missing_store(self):
        config = load_config()
        with self.assertRaises(ValueError):
            ReplayContext(**config)

    def test_init_invalid_endpoint(self):
        try:
            config = load_config()
            config['name'] = local_name
            config['persistent_store'] = mock.Mock()
            tmp = zmq.Context()
            placeholder = tmp.socket(zmq.REP)
            placeholder.bind('tcp://*:{0}'.format(
                config["replay_endpoints"][local_name].rsplit(':')[-1]
            ))
            with self.assertRaises(IOError):
                ReplayContext(**config)
        finally:
            placeholder.close()


class TestReplayContext(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.config['name'] = local_name
        self.config['persistent_store'] = mock.Mock()
        self.replay_context = ReplayContext(**self.config)
        self.request_context = zmq.Context()
        self.request_socket = self.request_context.socket(zmq.REQ)
        self.request_socket.connect(
            self.config['replay_endpoints'][local_name])

    def tearDown(self):
        self.request_socket.close()
        self.replay_context.publisher.close()

    @requires_network
    def test_get_replay(self):
        # Setup the store to return what we ask.
        answer = [{'foo': 'bar'}]
        self.config['persistent_store'].get = mock.Mock(side_effect=[answer])
        # Doesn't matter what we send as long as it is legit JSON,
        # since the store is mocked
        self.request_socket.send(u'{"id": 1}'.encode('utf-8'))
        self.replay_context._req_rep_cycle()

        rep = self.request_socket.recv_multipart()
        print(rep)
        print(answer)

        assert len(answer) == len(rep)
        for r, a in zip(rep, answer):
            self.assertDictEqual(json.loads(r.decode('utf-8')), a)

    @requires_network
    def test_get_error(self):
        # Setup the store to return what we ask.
        answer = ValueError('No luck!')
        self.config['persistent_store'].get = mock.Mock(side_effect=[answer])
        # Doesn't matter what we send as long as it is legit JSON,
        # since the store is mocked
        self.request_socket.send(u'{"id": 1}'.encode('utf-8'))
        self.replay_context._req_rep_cycle()

        rep = self.request_socket.recv_multipart()
        print(rep)

        assert len(rep) == 1 and "error: 'No luck!'" == rep[0].decode('utf-8')


class TestSqlStore(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.store = SqlStore(self.engine)
        msgs = [
            {
                "i": 0,
                "topic": "org.foo.bar",
                "msg_id": "11111111-1111-1111-1111-111111111111",
                "timestamp": 2,
                "seq_id": 1,
                "msg": {"foo": "bar"},
            },
            {
                "i": 1,
                "topic": "org.foo.bar",
                "msg_id": "22222222-2222-2222-2222-222222222222",
                "timestamp": 10,
                "seq_id": 2,
                "msg": {"foo": "baz"},
            }
        ]
        session = self.store.session_class()
        for m in msgs:
            session.add(SqlMessage(
                seq_id=m['seq_id'],
                uuid=m['msg_id'],
                timestamp=datetime.fromtimestamp(m['timestamp']),
                topic=m['topic'],
                msg=json.dumps(m)
            ))
        session.commit()

    def test_add(self):
        orig_msg = {
            "i": 2,
            "topic": "org.foo.bar",
            "msg_id": "33333333-3333-3333-3333-333333333333",
            "timestamp": 20,
            "msg": {"foo": "foo"}
        }
        # make a copy to avoid squewing the comparison
        ret = self.store.add(dict(orig_msg))

        orig_msg['seq_id'] = 3
        self.assertDictEqual(ret, orig_msg)

        session = self.store.session_class()
        sql_msg = session.query(SqlMessage)\
            .filter(SqlMessage.seq_id == 3).one()
        self.assertDictEqual(json.loads(sql_msg.msg), orig_msg)

    def test_get_seq_id(self):
        first = self.store.get({"seq_id": 1})
        assert len(first) == 1 and first[0]['i'] == 0

    def test_get_time(self):
        first, second = self.store.get({"time": [0, 15]})
        assert (
            (first['i'] == 0 and second['i'] == 1) or
            (first['i'] == 1 and second['i'] == 0))

    def test_get_wrong_seq_id(self):
        with self.assertRaises(ValueError):
            self.store.get({"seq_id": 18})

    def test_get_illformed_time(self):
        with self.assertRaises(ValueError):
            first, second = self.store.get({"time": [0, 15, 3]})


class ReplayThread(Thread):
    def __init__(self, context):
        self.stop = Event()
        self.context = context
        super(ReplayThread, self).__init__()

    def run(self):
        try:
            while not self.stop.is_set():
                self.context._req_rep_cycle()
        finally:
            self.context.publisher.close()


class TestGetReplay(unittest.TestCase):
    def setUp(self):
        self.config = load_config()
        self.config['name'] = local_name
        self.config['mute'] = True
        self.config['persistent_store'] = mock.Mock()
        self.replay_context = ReplayContext(**self.config)
        self.replay_thread = ReplayThread(self.replay_context)
        self.context = zmq.Context()

    def tearDown(self):
        self.replay_thread.stop.set()

    @requires_network
    def test_get_replay_no_available_endpoint(self):
        # self.replay_thread.start()
        with self.assertRaises(ValueError):
            list(get_replay("phony", {"seq_ids": [1, 2]}, self.config, self.context))

    @requires_network
    def test_get_replay_wrong_query(self):
        # We don't actually test with a wrong query, we just throw back an
        # error from the store.
        self.config['persistent_store'].get = mock.Mock(
            side_effect=[ValueError("this is an error")])
        self.replay_thread.start()
        with self.assertRaises(ValueError):
            list(get_replay(local_name, {"seq_ids": [1, 2]}, self.config, self.context))

    @requires_network
    def test_get_replay(self):
        # As before, the correctness of the query doesn't matter much
        # since it is taken care of on the server side.
        orig_msg = {
            "i": 2,
            "seq_id": 3,
            "topic": "org.foo.bar",
            "msg_id": "33333333-3333-3333-3333-333333333333",
            "timestamp": 20,
            "msg": {"foo": "foo"}
        }
        self.config['persistent_store'].get = mock.Mock(side_effect=[[orig_msg]])
        self.replay_thread.start()
        msgs = list(get_replay(
            local_name, {"seq_id": 3}, self.config, self.context
        ))
        assert len(msgs) == 1
        self.assertDictEqual(msgs[0], orig_msg)
