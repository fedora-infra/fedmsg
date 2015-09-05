# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
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

import pprint
import re
import time
import sys

import pygments
import pygments.lexers
import pygments.formatters
import six

import fedmsg
import fedmsg.encoding
import fedmsg.meta
from fedmsg.commands import BaseCommand
from fedmsg.utils import cowsay_output


class TailCommand(BaseCommand):
    """ Watch all endpoints on the bus and print each message to stdout. """

    name = "fedmsg-tail"
    extra_args = [
        (['--topic'], {
            'dest': 'topic',
            'help': 'The topic pattern to listen for.  Everything by default.',
            'default': '',
        }),
        (['--query'], {
            'dest': 'query',
            'help': 'Displays only the element of the message specified.',
            'type': str,
            'default': None
        }),
        (['--pretty'], {
            'dest': 'pretty',
            'help': 'Pretty print the JSON messages.',
            'default': False,
            'action': 'store_true',
        }),
        (['--really-pretty'], {
            'dest': 'really_pretty',
            'help': 'Extra-pretty print the JSON messages.',
            'default': False,
            'action': 'store_true',
        }),
        (['--cowsay'], {
            'dest': 'cowsay',
            'help': 'Print cowsay output of messages',
            'default': False,
            'action': 'store_true',
        }),
        (['--terse'], {
            'dest': 'terse',
            'help': 'Print "english" representations of messages only.',
            'default': False,
            'action': 'store_true',
        }),
        (['--exclude'], {
            'dest': 'exclusive_regexp',
            'metavar': 'REGEXP',
            'help': 'Only show topics that do not match the supplied regexp.',
            'default': '_heartbeat',
        }),
        (['--include'], {
            'dest': 'inclusive_regexp',
            'metavar': 'REGEXP',
            'help': 'Only show topics that match the supplied regexp.',
            'default': '^((?!_heartbeat).)*$',
        }),
        (['--users'], {
            'dest': 'users',
            'metavar': 'USERS',
            'default': None,
            'help': 'A comma-separated list of usernames.  Show only messages'
            'related to these users.',
        }),
        (['--packages'], {
            'dest': 'packages',
            'metavar': 'PACKAGES',
            'default': None,
            'help': 'A comma-separated list of packages.  Show only messages'
            'related to these packages.',
        }),
        (['--validate'], {
            'dest': 'validate_signatures',
            'default': None,
            'help': 'Override the \'validate_signatures\' configuration value'
            'to be True so that X509 certificates in messages are validated.',
            'action': 'store_true',
        }),
        (['--no-validate'], {
            'dest': 'validate_signatures',
            'default': None,
            'help': 'Override the \'validate_signatures\' configuration value'
            'to be False so that X509 certificates in messages are ignored.',
            'action': 'store_false',
        }),

    ]

    def run(self):
        # Disable sending
        self.config['publish_endpoint'] = None

        # Disable timeouts.  We want to tail forever!
        self.config['timeout'] = 0

        # Even though fedmsg-tail won't be sending any messages, give it a
        # name to conform with the other commands.
        self.config['name'] = 'relay_inbound'

        # Tail is never going to send any messages, so we suppress warnings
        # about having no publishing sockets established.
        self.config['mute'] = True

        fedmsg.init(**self.config)

        # Build a message formatter
        formatter = lambda d: d
        if self.config['pretty']:
            def formatter(d):
                d['timestamp'] = time.ctime(d['timestamp'])
                d = fedmsg.crypto.strip_credentials(d)
                return "\n" + pprint.pformat(d)

        if self.config['really_pretty']:
            def formatter(d):
                d = fedmsg.crypto.strip_credentials(d)
                fancy = pygments.highlight(
                    fedmsg.encoding.pretty_dumps(d),
                    pygments.lexers.JavascriptLexer(),
                    pygments.formatters.TerminalFormatter()
                ).strip()
                return "\n" + fancy

        if self.config['query']:
            def formatter(d):
                result = fedmsg.utils.dict_query(d, self.config['query'])
                return ", ".join([six.text_type(value) for value in result.values()])

        if self.config['terse']:
            formatter = lambda d: "\n" + fedmsg.meta.msg2repr(d, **self.config)

        if self.config['cowsay']:
            def formatter(d):
                result, error = cowsay_output(fedmsg.meta.msg2subtitle(d, **self.config))
                if not error:
                    return "\n" + result
                else:
                    return "\n" + error

        # Build regular expressions for use in our loop.
        exclusive_regexp = re.compile(self.config['exclusive_regexp'])
        inclusive_regexp = re.compile(self.config['inclusive_regexp'])

        # Build username and package filter sets for use in our loop.
        users, packages = set(), set()
        if self.config['users']:
            users = set(map(str.strip, self.config['users'].split(',')))
        if self.config['packages']:
            packages = set(map(str.strip, self.config['packages'].split(',')))

        # Only initialize this if we have to
        if users or packages or self.config['terse'] or self.config['cowsay']:
            fedmsg.meta.make_processors(**self.config)

        # Spin up a zmq.Poller and yield messages
        for name, ep, topic, message in fedmsg.tail_messages(**self.config):
            if exclusive_regexp.search(topic):
                continue

            if not inclusive_regexp.search(topic):
                continue

            if users:
                actual = fedmsg.meta.msg2usernames(message, **self.config)
                if not users.intersection(actual):
                    continue

            if packages:
                actual = fedmsg.meta.msg2packages(message, **self.config)
                if not packages.intersection(actual):
                    continue

            output = formatter(message)
            if output:
                self.log.info(output)


def tail():
    command = TailCommand()
    return command.execute()
