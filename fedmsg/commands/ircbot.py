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
# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels.  See fedmsg-config.py for options.
from fedmsg.commands import command

from fedmsg.consumers.ircbot import IRCBotConsumer

extra_args = []


@command(name="fedmsg-irc", extra_args=extra_args, daemonizable=True)
def ircbot(**kw):
    """ Relay messages from the bus to any number of IRC channels.

    This is highly configurable by way of the :term:`irc` config value.
    """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_subscribe_endpoints=','.join(
            ','.join(bunch) for bunch in kw['endpoints'].values()
        ),
    )
    kw.update(moksha_options)

    kw[IRCBotConsumer.config_key] = True

    from moksha.hub import main
    main(options=kw, consumers=[IRCBotConsumer])
