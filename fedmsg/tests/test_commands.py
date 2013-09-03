import unittest
from mock import Mock
from mock import patch
from datetime import datetime
import time
import json
import os

import fedmsg
import fedmsg.core
import fedmsg.config
import fedmsg.commands

from fedmsg.commands.logger import LoggerCommand
from fedmsg.commands.tail import TailCommand
from fedmsg.commands.relay import RelayCommand
import fedmsg.consumers.relay

from nose.tools import eq_

import threading

import six


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.local = threading.local()

        # Crazy.  I'm sorry.
        os.environ['TZ'] = 'US/Central'
        time.tzset()

    def tearDown(self):
        del self.local
        self.local = None

    @patch("sys.argv", new_callable=lambda: ["fedmsg-logger"])
    @patch("sys.stdout", new_callable=six.StringIO)
    def test_logger_basic(self, stdout, argv):

        test_input = "a message for you"

        if six.PY3:
            stdin = lambda: six.StringIO(test_input)
        else:
            stdin = lambda: six.StringIO(test_input.encode('utf-8'))

        msgs = []

        def mock_publish(context, topic=None, msg=None, modname=None):
            msgs.append(msg)

        config = {}
        with patch("fedmsg.__local", self.local):
            with patch("fedmsg.config.__cache", config):
                with patch("fedmsg.core.FedMsgContext.publish", mock_publish):
                    with patch("sys.stdin", new_callable=stdin):
                        command = LoggerCommand()
                        command.execute()

        eq_(msgs, [{'log': test_input}])

    @patch("sys.argv", new_callable=lambda: ["fedmsg-logger", "--json-input"])
    @patch("sys.stdout", new_callable=six.StringIO)
    def test_logger_json(self, stdout, argv):

        test_input_dict = {"hello": "world"}
        test_input = json.dumps(test_input_dict)

        if six.PY3:
            stdin = lambda: six.StringIO(test_input)
        else:
            stdin = lambda: six.StringIO(test_input.encode('utf-8'))

        msgs = []

        def mock_publish(context, topic=None, msg=None, modname=None):
            msgs.append(msg)

        config = {}
        with patch("fedmsg.__local", self.local):
            with patch("fedmsg.config.__cache", config):
                with patch("fedmsg.core.FedMsgContext.publish", mock_publish):
                    with patch("sys.stdin", new_callable=stdin):
                        command = LoggerCommand()
                        command.execute()

        eq_(msgs, [test_input_dict])

    @patch("sys.argv", new_callable=lambda: ["fedmsg-tail"])
    @patch("sys.stdout", new_callable=six.StringIO)
    def test_tail_basic(self, stdout, argv):
        def mock_tail(self, topic="", passive=False, **kw):
            yield ("name", "endpoint", "topic", dict(topic="topic"))

        config = {}
        with patch("fedmsg.__local", self.local):
            with patch("fedmsg.config.__cache", config):
                with patch("fedmsg.core.FedMsgContext.tail_messages",
                           mock_tail):
                    command = fedmsg.commands.tail.TailCommand()
                    command.execute()

        output = stdout.getvalue()
        expected = "{'topic': 'topic'}\n"
        assert(output.endswith(expected))

    @patch("sys.argv", new_callable=lambda: ["fedmsg-tail", "--pretty"])
    @patch("sys.stdout", new_callable=six.StringIO)
    def test_tail_pretty(self, stdout, argv):
        msgs = []

        def mock_tail(self, topic="", passive=False, **kw):
            msg = dict(
                msg=dict(hello="world"),
                msg_id='2ad5aaf8-68af-4a6d-9196-2a8b43a73238',
                timestamp=1354563717.472648,  # Once upon a time...
                topic="org.threebean.prod.testing",
            )

            yield ("name", "endpoint", "topic", msg)

        config = {}
        with patch("fedmsg.__local", self.local):
            with patch("fedmsg.config.__cache", config):
                with patch("fedmsg.core.FedMsgContext.tail_messages",
                           mock_tail):
                    command = fedmsg.commands.tail.TailCommand()
                    command.execute()

        output = stdout.getvalue()
        expected = "{'msg': {'hello': 'world'},"
        assert(expected in output)

    @patch("sys.argv", new_callable=lambda: ["fedmsg-tail", "--really-pretty"])
    @patch("sys.stdout", new_callable=six.StringIO)
    def test_tail_really_pretty(self, stdout, argv):
        msgs = []

        def mock_tail(self, topic="", passive=False, **kw):
            msg = dict(
                msg=dict(hello="world"),
                msg_id='2ad5aaf8-68af-4a6d-9196-2a8b43a73238',
                timestamp=1354563717.472648,  # Once upon a time...
                topic="org.threebean.prod.testing",
            )

            yield ("name", "endpoint", "topic", msg)

        config = {}
        with patch("fedmsg.__local", self.local):
            with patch("fedmsg.config.__cache", config):
                with patch("fedmsg.core.FedMsgContext.tail_messages",
                           mock_tail):
                    command = fedmsg.commands.tail.TailCommand()
                    command.execute()

        output = stdout.getvalue()
        expected = \
            '\x1b[33m"hello"\x1b[39;49;00m:\x1b[39;49;00m \x1b[39;49;00m' + \
            '\x1b[33m"world"\x1b[39;49;00m'

        assert(expected in output)

    @patch("sys.argv", new_callable=lambda: ["fedmsg-relay"])
    def test_relay(self, argv):
        actual_options = []

        def mock_main(options, consumers, framework):
            actual_options.append(options)

        config = {}
        with patch("fedmsg.__local", self.local):
            with patch("fedmsg.config.__cache", config):
                with patch("moksha.hub.main", mock_main):
                    command = fedmsg.commands.relay.RelayCommand()
                    command.execute()

        actual_options = actual_options[0]
        assert(
            fedmsg.consumers.relay.RelayConsumer.config_key in actual_options
        )
        assert(
            actual_options[fedmsg.consumers.relay.RelayConsumer.config_key]
        )
