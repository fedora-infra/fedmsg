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
#           Ryan Brown
#
# -*- coding; utf-8 -*-
"""
Description: A bot that takes a config and puts messages matching given
regexes in specified IRC channels.  See :term:`irc` for options.

Think of it like a one-way firehose that spews fedmsg messages to IRC.
"""

from fedmsg.commands import BaseCommand
from fedmsg.consumers.ircbot import IRCBotConsumer


class IRCCommand(BaseCommand):
    """ Relay messages from the bus to any number of IRC channels.

    This is highly configurable by way of the :term:`irc` config value.
    """

    name = "fedmsg-irc"
    extra_args = []
    daemonizable = True

    def run(self):
        # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to
        # work with moksha's expected configuration.
        moksha_options = dict(
            zmq_subscribe_endpoints=','.join(
                ','.join(bunch) for bunch in self.config['endpoints'].values()
            ),
        )
        self.config.update(moksha_options)

        self.config[IRCBotConsumer.config_key] = True

        from moksha.hub import main
        main(
            # Pass in our config dict
            options=self.config,
            # Only run this *one* consumer
            consumers=[IRCBotConsumer],
            # Tell moksah to quiet its logging
            framework=False,
        )


def ircbot():
    command = IRCCommand()
    command.execute()
