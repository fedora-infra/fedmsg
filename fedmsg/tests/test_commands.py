import unittest
from mock import Mock
from mock import patch
from datetime import datetime
import json
import os

import fedmsg.core
import fedmsg.config
import fedmsg.commands
from fedmsg.commands.logger import LoggerCommand
from nose.tools import eq_

import six


class TestCommands(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch("sys.argv", new_callable=lambda: ["fedmsg-logger"])
    @patch("sys.stdout", new_callable=six.StringIO)
    def test_logger(self, stdout, argv):

        test_input = "a message for you"

        if six.PY3:
            stdin = lambda: six.StringIO(test_input)
        else:
            stdin = lambda: six.StringIO(test_input.encode('utf-8'))

        msgs = []

        def mock_publish(context, topic=None, msg=None, modname=None):
            msgs.append(msg)

        with patch("fedmsg.core.FedMsgContext.publish", mock_publish):
            with patch("sys.stdin", new_callable=stdin):
                command = fedmsg.commands.logger.LoggerCommand()
                command.execute()

        eq_(msgs, [{'log': test_input}])
