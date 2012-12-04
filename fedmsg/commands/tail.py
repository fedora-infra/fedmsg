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
import pprint
import re
import time

import pygments
import pygments.lexers
import pygments.formatters

import fedmsg
import fedmsg.encoding
import fedmsg.meta
from fedmsg.commands import BaseCommand


class TailCommand(BaseCommand):
    """ Watch all endpoints on the bus and print each message to stdout. """
    name="fedmsg-tail"
    extra_args = [
        (['--topic'], {
            'dest': 'topic',
            'help': 'The topic pattern to listen for.  Everything by default.',
            'default': '',
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
        (['--terse'], {
            'dest': 'terse',
            'help': 'Print "english" representations of messages only.',
            'default': False,
            'action': 'store_true',
        }),
        (['--filter'], {
            'dest': 'exclusive_regexp',
            'metavar': 'REGEXP',
            'help': 'Only show topics that do not match the supplied regexp.',
            'default': '_heartbeat',
        }),
        (['--regexp'], {
            'dest': 'inclusive_regexp',
            'metavar': 'REGEXP',
            'help': 'Only show topics that match the supplied regexp.',
            'default': '^((?!_heartbeat).)*$',
        }),
    ]
    def run(self):
        # Disable sending
        self.config['publish_endpoint'] = None

        # Disable timeouts.  We want to tail forever!
        self.config['timeout'] = 0

        # Even though fedmsg-tail won't be sending any messages, give it a name to
        # conform with the other commands.
        self.config['name'] = 'relay_inbound'

        # Tail is never going to send any messages, so we suppress warnings about
        # having no publishing sockets established.
        self.config['mute'] = True

        fedmsg.init(**self.config)
        fedmsg.meta.make_processors(**self.config)

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

        if self.config['terse']:
            formatter = lambda d: "\n" + fedmsg.meta.msg2repr(d, **self.config)

        exclusive_regexp = re.compile(self.config['exclusive_regexp'])
        inclusive_regexp = re.compile(self.config['inclusive_regexp'])

        # The "proper" fedmsg way to do this would be to spin up or connect to an
        # existing Moksha Hub and register a consumer on the "*" topic that simply
        # prints out each message it consumes.  That seems like overkill, so we're
        # just going to directly access the endpoints ourself.

        for name, ep, topic, message in fedmsg.tail_messages(**self.config):
            if exclusive_regexp.search(topic):
                continue

            if not inclusive_regexp.search(topic):
                continue

            self.log.info("%s, %s, %s, %s" % (name, ep, topic, formatter(message)))

def tail():
    command = TailCommand()
    return command.execute()
