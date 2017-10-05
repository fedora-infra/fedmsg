# -*- coding: utf-8 -*-
#
# This file is part of fedmsg.
# Copyright (C) 2017 Red Hat, Inc.
# Copyright (C) 2014 Nicolas Dandrimont
# Copyright (C) 2015 Slavek Kabrda
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

import resource
import shutil
import tempfile
import threading
import unittest
import time
import json
import os
import mock

from click.testing import CliRunner
import six
import zmq

import fedmsg
import fedmsg.core
import fedmsg.config
import fedmsg.commands
from fedmsg.commands.hub import HubCommand
from fedmsg.commands.logger import LoggerCommand
from fedmsg.commands.tail import TailCommand
from fedmsg.commands.config import config as config_command
from fedmsg.commands.check import check
import fedmsg.consumers.relay


CONF_FILE = os.path.join(os.path.dirname(__file__), "fedmsg.d", "ircbot.py")


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.local = threading.local()

        # Crazy.  I'm sorry.
        os.environ['TZ'] = 'US/Central'
        time.tzset()

    def tearDown(self):
        del self.local
        self.local = None

    @mock.patch("sys.argv", new_callable=lambda: ["fedmsg-logger"])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_logger_basic(self, stdout, argv):

        test_input = "a message for you"

        def mock_stdin():
            if six.PY3:
                return six.StringIO(test_input)
            else:
                return six.StringIO(test_input.encode('utf-8'))

        stdin = mock_stdin

        msgs = []

        def mock_publish(context, topic=None, msg=None, modname=None):
            msgs.append(msg)

        config = {}
        with mock.patch("fedmsg.__local", self.local):
            with mock.patch("fedmsg.config.__cache", config):
                with mock.patch("fedmsg.core.FedMsgContext.publish", mock_publish):
                    with mock.patch("sys.stdin", new_callable=stdin):
                        command = LoggerCommand()
                        command.execute()

        self.assertEqual(msgs, [{'log': test_input}])

    @mock.patch("sys.argv", new_callable=lambda: ["fedmsg-logger", "--json-input"])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_logger_json(self, stdout, argv):

        test_input_dict = {"hello": "world"}
        test_input = json.dumps(test_input_dict)

        def mock_stdin():
            if six.PY3:
                return six.StringIO(test_input)
            else:
                return six.StringIO(test_input.encode('utf-8'))

        stdin = mock_stdin

        msgs = []

        def mock_publish(context, topic=None, msg=None, modname=None):
            msgs.append(msg)

        config = {}
        with mock.patch("fedmsg.__local", self.local):
            with mock.patch("fedmsg.config.__cache", config):
                with mock.patch("fedmsg.core.FedMsgContext.publish", mock_publish):
                    with mock.patch("sys.stdin", new_callable=stdin):
                        command = LoggerCommand()
                        command.execute()

        self.assertEqual(msgs, [test_input_dict])

    @mock.patch("sys.argv", new_callable=lambda: ["fedmsg-tail"])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_tail_basic(self, stdout, argv):
        def mock_tail(self, topic="", passive=False, **kw):
            yield ("name", "endpoint", "topic", dict(topic="topic"))

        config = {}
        with mock.patch("fedmsg.__local", self.local):
            with mock.patch("fedmsg.config.__cache", config):
                with mock.patch(
                        "fedmsg.core.FedMsgContext.tail_messages", mock_tail):
                    command = TailCommand()
                    command.execute()

        output = stdout.getvalue()
        expected = "{'topic': 'topic'}\n"
        assert(output.endswith(expected))

    @mock.patch("sys.argv", new_callable=lambda: ["fedmsg-tail", "--pretty"])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_tail_pretty(self, stdout, argv):

        def mock_tail(self, topic="", passive=False, **kw):
            msg = dict(
                msg=dict(hello="world"),
                msg_id='2ad5aaf8-68af-4a6d-9196-2a8b43a73238',
                timestamp=1354563717.472648,  # Once upon a time...
                topic="org.threebean.prod.testing",
            )
            yield ("name", "endpoint", "topic", msg)

        config = {}
        with mock.patch("fedmsg.__local", self.local):
            with mock.patch("fedmsg.config.__cache", config):
                with mock.patch(
                        "fedmsg.core.FedMsgContext.tail_messages", mock_tail):
                    command = TailCommand()
                    command.execute()

        output = stdout.getvalue()
        expected = "{'msg': {'hello': 'world'},"
        assert(expected in output)

    @mock.patch("sys.argv", new_callable=lambda: ["fedmsg-tail", "--really-pretty"])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_tail_really_pretty(self, stdout, argv):

        def mock_tail(self, topic="", passive=False, **kw):
            msg = dict(
                msg=dict(hello="world"),
                msg_id='2ad5aaf8-68af-4a6d-9196-2a8b43a73238',
                timestamp=1354563717.472648,  # Once upon a time...
                topic="org.threebean.prod.testing",
            )

            yield ("name", "endpoint", "topic", msg)

        config = {}
        with mock.patch("fedmsg.__local", self.local):
            with mock.patch("fedmsg.config.__cache", config):
                with mock.patch(
                        "fedmsg.core.FedMsgContext.tail_messages", mock_tail):
                    command = TailCommand()
                    command.execute()

        output = stdout.getvalue()
        expected = '\x1b[33m"hello"\x1b[39;49;00m'
        assert(expected in output)

    @mock.patch("sys.argv", new_callable=lambda: ["fedmsg-config"])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_config_basic(self, stdout, argv):
        with mock.patch('fedmsg.config.__cache', {}):
            config_command()

        output = stdout.getvalue()
        output_conf = json.loads(output)

        with mock.patch('fedmsg.config.__cache', {}):
            fedmsg_conf = fedmsg.config.load_config()

        self.assertEqual(output_conf, fedmsg_conf)

    @mock.patch("sys.argv", new_callable=lambda: [
        "fedmsg-config", "--query", "endpoints",
    ])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_config_query(self, stdout, argv):
        with mock.patch('fedmsg.config.__cache', {}):
            config_command()

        output = stdout.getvalue()
        output_conf = json.loads(output)

        with mock.patch('fedmsg.config.__cache', {}):
            fedmsg_conf = fedmsg.config.load_config()

        self.assertEqual(output_conf, fedmsg_conf["endpoints"])

    @mock.patch("sys.argv", new_callable=lambda: [
        "fedmsg-config", "--query", "endpoints.broken",
    ])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    @mock.patch("sys.stderr", new_callable=six.StringIO)
    def test_config_query_broken(self, stderr, stdout, argv):
        try:
            with mock.patch('fedmsg.config.__cache', {}):
                config_command()
        except SystemExit as exc:
            self.assertEqual(exc.code, 1)
        else:
            output = "output: %r, error: %r" % (
                stdout.getvalue(), stderr.getvalue())
            assert False, output

        output = stdout.getvalue()
        error = stderr.getvalue()

        self.assertEqual(output.strip(), "")
        self.assertEqual(error.strip(), "Key `endpoints.broken` does not exist in config")

    @mock.patch("sys.argv", new_callable=lambda: [
        "fedmsg-config", "--disable-defaults", "--config-filename", CONF_FILE,
    ])
    @mock.patch("sys.stdout", new_callable=six.StringIO)
    def test_config_single_file(self, stdout, argv):
        with mock.patch('fedmsg.config.__cache', {}):
            config_command()

        output = stdout.getvalue()
        output_conf = json.loads(output)

        with mock.patch('fedmsg.config.__cache', {}):
            fedmsg_conf = fedmsg.config.load_config(
                filenames=[CONF_FILE],
                disable_defaults=True,
            )

        self.assertEqual(output_conf, fedmsg_conf)


@mock.patch('fedmsg.commands.dictConfig', autospec=True)
@mock.patch('fedmsg.config.load_config', autospec=True)
@mock.patch('fedmsg.commands.hub.resource.setrlimit', autospec=True)
class TestHubsCommand(unittest.TestCase):

    def test_setting_nofile_limit(self, mock_setrlimit, *unused_mocks):
        """Assert setting the default rlimit works."""
        hub_command = HubCommand()
        hub_command.set_rlimit_nofiles(limit=1)
        mock_setrlimit.assert_called_once_with(
            resource.RLIMIT_NOFILE, (1, 1))

    def test_setting_bad_nofile_limit(self, mock_setrlimit, *unused_mocks):
        """Assert that setting a rlimit greater than allow is handled well."""
        mock_setrlimit.side_effect = ValueError('No files for you')
        hub_command = HubCommand()
        hub_command.log = mock.Mock()
        hub_command.set_rlimit_nofiles(limit=1844674407370)
        hub_command.log.warning.assert_called_once()

    def test_setting_nofile_limit_os_fail(self, mock_setrlimit, *unused_mocks):
        """Assert that setting a rlimit greater than allow is handled well."""
        mock_setrlimit.side_effect = resource.error('No files for you')
        hub_command = HubCommand()
        hub_command.log = mock.Mock()
        hub_command.set_rlimit_nofiles(limit=1844674407370)
        hub_command.log.warning.assert_called_once()


class CheckTests(unittest.TestCase):
    """Tests for the :class:`fedmsg.commands.check.CheckCommand`."""

    def setUp(self):
        self.report = {
            "consumers": [
                {
                    "backlog": 0,
                    "exceptions": 0,
                    "headcount_in": 0,
                    "headcount_out": 0,
                    "initialized": True,
                    "jsonify": True,
                    "module": "test.consumers",
                    "name": "TestConsumer",
                    "times": [],
                    "topic": ['test']
                },
            ],
            "producers": [
                 {
                   "exceptions": 0,
                   "frequency": 5,
                   "initialized": True,
                   "last_ran": 1496780847.269628,
                   "module": "moksha.hub.monitoring",
                   "name": "MonitoringProducer",
                   "now": False,
                 }
            ]
        }
        self.tempdir = tempfile.mkdtemp()
        self.socket_path = 'ipc://' + os.path.join(self.tempdir, self.id().split('.')[-1])

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def send_report(self):
        """Set up a socket in thread and send a report for several seconds."""
        def report_in_thread():
            context = zmq.Context.instance()
            socket = context.socket(zmq.PUB)
            socket.setsockopt(zmq.LINGER, 0)
            socket.bind(self.socket_path)
            for x in range(0, 3):
                socket.send(json.dumps(self.report).encode('utf-8'))
                time.sleep(1)
            socket.close()

        thread = threading.Thread(target=report_in_thread)
        thread.start()

    def test_no_monitor_endpoint(self):
        """Assert that when no endpoint for monitoring is configured, users are informed."""
        expected_error = (
            u'Error: No monitoring endpoint has been configured: please set '
            u'"moksha.monitoring.socket"\n'
        )
        runner = CliRunner()
        result = runner.invoke(check, [])
        self.assertEqual(1, result.exit_code)
        self.assertEqual(expected_error, result.output)

    @mock.patch('fedmsg.commands.check.load_config')
    def test_socket_timeout(self, mock_load_config):
        """Assert when no message is received a timeout is hit."""
        mock_load_config.return_value = {
            'moksha.monitoring.socket': self.socket_path
        }
        expected_error = (
            u'Error: Failed to receive message from the monitoring endpoint'
            u' ({path}) in 1 seconds.\n'.format(path=self.socket_path)
        )
        runner = CliRunner()
        context = zmq.Context.instance()
        socket = context.socket(zmq.PUB)
        socket.setsockopt(zmq.LINGER, 0)
        socket.bind(self.socket_path)

        result = runner.invoke(check, ['--timeout=1'])

        self.assertEqual(expected_error, result.output)
        self.assertEqual(1, result.exit_code)
        socket.close()

    @mock.patch('fedmsg.commands.check.load_config')
    def test_no_consumers_or_producers(self, mock_load_config):
        """Assert that when no consumers or producers are specified, all are displayed."""
        mock_load_config.return_value = {'moksha.monitoring.socket': self.socket_path}
        runner = CliRunner()
        expected_output = (u'No consumers or producers specified so all will be shown.'
                           u'\n{r}\n'.format(r=json.dumps(self.report, indent=2, sort_keys=True)))

        self.send_report()
        result = runner.invoke(check, [])

        self.assertEqual(expected_output, result.output)
        self.assertEqual(0, result.exit_code)

    @mock.patch('fedmsg.commands.check.load_config')
    def test_missing(self, mock_load_config):
        """
        Assert the command has a non-zero exit when a consumer is missing
        from the list of active consumers.
        """
        mock_load_config.return_value = {'moksha.monitoring.socket': self.socket_path}
        runner = CliRunner()
        expected_output = (
            u'"MissingConsumer" is not active!\n'
            u'Error: Some consumers and/or producers are missing!\n'
        )

        self.send_report()
        result = runner.invoke(check, ['--consumer=MissingConsumer'])

        self.assertEqual(1, result.exit_code)
        self.assertEqual(expected_output, result.output)

    @mock.patch('fedmsg.commands.check.load_config')
    def test_uninitialized(self, mock_load_config):
        """Assert the command has a non-zero exit when a consumer is not initialized."""
        mock_load_config.return_value = {'moksha.monitoring.socket': self.socket_path}
        runner = CliRunner()
        expected_output = (
            u'"TestConsumer" is not initialized!\n'
            u'Error: Some consumers and/or producers are uninitialized!\n'
        )
        self.report['consumers'][0]['initialized'] = False

        self.send_report()
        result = runner.invoke(check, ['--consumer=TestConsumer'])

        self.assertEqual(expected_output, result.output)
        self.assertEqual(1, result.exit_code)

    @mock.patch('fedmsg.commands.check.load_config')
    def test_all_good(self, mock_load_config):
        """Assert if all consumers/producers are present, the command exits 0."""
        mock_load_config.return_value = {'moksha.monitoring.socket': self.socket_path}
        runner = CliRunner()
        expected_output = (u'All consumers and producers are active!\n'
                           u'{r}\n'.format(r=json.dumps(self.report, indent=2, sort_keys=True)))

        self.send_report()
        result = runner.invoke(check, ['--consumer=TestConsumer'])

        self.assertEqual(0, result.exit_code)
        self.assertEqual(expected_output, result.output)
