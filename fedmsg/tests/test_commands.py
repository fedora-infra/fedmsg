import unittest
from mock import Mock
from mock import patch
from datetime import datetime
import json
import os

import fedmsg
import fedmsg.core
import fedmsg.config
import fedmsg.commands
from fedmsg.commands.logger import LoggerCommand
from nose.tools import eq_

import threading

import six


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.local = threading.local()

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
                        command = fedmsg.commands.logger.LoggerCommand()
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
                        command = fedmsg.commands.logger.LoggerCommand()
                        command.execute()

        eq_(msgs, [test_input_dict])
