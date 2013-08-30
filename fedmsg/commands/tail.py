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

import itertools
import os
import pprint
import re
import urllib
import time
import math

import pygments
import pygments.lexers
import pygments.formatters

import fedmsg
import fedmsg.encoding
import fedmsg.meta
from fedmsg.commands import BaseCommand


def _cache_avatar(username, url, directory):
    """ Utility to grab avatars from outerspace for the --gource option. """

    fname = os.path.join(directory, "%s.jpg" % username)
    if os.path.exists(fname):
        # We already have it cached.  Just chill.
        pass
    else:
        # Make sure we have a place to write it
        if os.path.isdir(directory):
            # We've been here before... that's good.
            pass
        else:
            os.makedirs(directory)

        # Grab it from the net and write to local cache on disk.
        try:
            urllib.urlretrieve(url, fname)
        except IOError:
            # If we can't talk to gravatar.com, try not to crash.
            pass


class TailCommand(BaseCommand):
    """ Watch all endpoints on the bus and print each message to stdout. """

    name = "fedmsg-tail"
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
        (['--gource'], {
            'dest': 'gource',
            'help': 'Print a live "git log" of the bus suitable for '
            'piping into the "gource" tool.',
            'default': False,
            'action': 'store_true',
        }),
        (['--gource-user-image-dir'], {
            'dest': 'gource_user_image_dir',
            'help': 'Directory to store user avatar images for --gource',
            'default': os.path.expanduser("~/.cache/avatar"),
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

        if self.config['gource']:
            # Output strings suitable for consumption by the "gource" tool.

            # We have 8 colors here and an unknown number of message types.
            # (There were 14 message types at the time this code was written).
            # Here we build a dict that maps message type names (a.k.a modnames
            # or services) to hex colors for usage in the gource graph.  We
            # wrap-around that dict if there are more message types than
            # there are colors (which there almost certainly are).
            procs = [proc.__name__.lower() for proc in fedmsg.meta.processors]
            colors = ["FFFFFF", "008F37", "FF680A", "CC4E00",
                      "8F0058", "8F7E00", "37008F", "7E008F"]
            n_wraps = 1 + int(math.ceil(len(colors) / float(len(procs))))
            colors = colors * n_wraps
            color_lookup = dict(zip(procs, colors))

            cache_directory = self.config['gource_user_image_dir']

            # After all that color trickiness, here is our formatter we'll use.
            def formatter(message):
                """ Use this like::

                  $ fedmsg-tail --gource | gource \
                          -i 0 \
                          --user-image-dir ~/.cache/avatar/ \
                          --log-format custom -
                """
                proc = fedmsg.meta.msg2processor(message, **self.config)
                avatars = fedmsg.meta.msg2avatars(message, **self.config)
                objs = fedmsg.meta.msg2objects(message, **self.config)
                name = proc.__name__.lower()

                lines = []
                for user, obj in itertools.product(avatars.keys(), objs):
                    _cache_avatar(user, avatars[user], cache_directory)
                    lines.append("%i|%s|A|%s|%s" % (
                        message['timestamp'],
                        user,
                        name + "/" + obj,
                        color_lookup[name],
                    ))
                return "\n".join(lines)

        # Build regular expressions for use in our loop.
        exclusive_regexp = re.compile(self.config['exclusive_regexp'])
        inclusive_regexp = re.compile(self.config['inclusive_regexp'])

        # Build username and package filter sets for use in our loop.
        users, packages = set(), set()
        if self.config['users']:
            users = set(map(str.strip, self.config['users'].split(',')))
        if self.config['packages']:
            packages = set(map(str.strip, self.config['packages'].split(',')))

        # Spin up a zmq.Poller and yield messages
        for name, ep, topic, message in fedmsg.tail_messages(**self.config):
            if exclusive_regexp.search(topic):
                continue

            if not inclusive_regexp.search(topic):
                continue

            actual_users = fedmsg.meta.msg2usernames(message, **self.config)
            if users and not users.intersection(actual_users):
                continue

            actual_packages = fedmsg.meta.msg2packages(message, **self.config)
            if packages and not packages.intersection(actual_packages):
                continue

            self.log.info(formatter(message))


def tail():
    command = TailCommand()
    return command.execute()
