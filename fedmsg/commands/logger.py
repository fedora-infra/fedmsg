# This file is part of fedmsg.
# Copyright (C) 2012 - 2015 Red Hat, Inc.
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
import sys

import fedmsg
import fedmsg.encoding
from fedmsg.commands import BaseCommand


class LoggerCommand(BaseCommand):
    """
    Emit log messages to the FI bus.

    If the fedmsg-relay service is not running at the address specified in
    the config, then this command will *hang* until that service becomes
    available.

    If --message is not specified, this command accepts messages from stdin.

    Some examples::

        $ echo '{"a": 1}' | fedmsg-logger --json-input
        $ echo "Hai there." | fedmsg-logger --modname=git --topic=repo.update
        $ fedmsg-logger --message="This is a message."
        $ fedmsg-logger --message='{"a": 1}' --json-input

    Note that when using --json-input, you must send valid JSON, including
    the use of double quotes as opposed to single quotes:

        '{"a": 1}' is good.
        "{'a': 1}" is bad.

    """
    name = 'fedmsg-logger'
    extra_args = [
        (['--message'], {
            'dest': 'logger_message',
            'help': "The message to send.",
        }),
        (['--json-input'], {
            'dest': 'json_input',
            'action': 'store_true',
            'default': False,
            'help': "Take each line of input as JSON.",
        }),
        (['--topic'], {
            'dest': 'topic',
            'metavar': "TOPIC",
            'default': "log",
            'help': "Think org.fedoraproject.dev.logger.TOPIC",
        }),
        (['--modname'], {
            'dest': 'modname',
            'metavar': "MODNAME",
            'default': "logger",
            'help': "More control over the topic. Think org.fp.MODNAME.TOPIC.",
        }),
        (['--cert-prefix'], {
            'dest': 'cert_prefix',
            'metavar': "CERT_PREFIX",
            'default': "shell",
            'help': "Specify a different cert from /etc/pki/fedmsg",
        }),
    ]

    def _log_message(self, kw, message):
        if kw['json_input']:
            msg = fedmsg.encoding.loads(message)
        else:
            msg = {'log': message}

        fedmsg.publish(
            topic=kw['topic'],
            msg=msg,
            modname=kw['modname'],
        )

    def __init__(self):
        super(LoggerCommand, self).__init__()

    def run(self):
        self.config['active'] = True
        self.config['name'] = 'relay_inbound'
        fedmsg.init(**self.config)

        if self.config.get('logger_message'):
            self._log_message(self.config, self.config.get('logger_message'))
        else:
            line = sys.stdin.readline()
            while line:
                self._log_message(self.config, line.strip())
                line = sys.stdin.readline()


def logger():
    command = LoggerCommand()
    return command.execute()
