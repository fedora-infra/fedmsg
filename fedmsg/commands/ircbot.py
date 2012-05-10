#!/usr/bin/env python
# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels
from fedmsg.commands import command

extra_args = [
    (['--channel'], {
        'dest': 'channel',
        'help': "The channel to join",
    }),
]


@command(extra_args=extra_args)
def ircbot(**kw):
    """ Relay connections from active loggers to the bus. """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_subscribe_endpoints=','.join(kw['endpoints'].values()),
    )
    kw.update(moksha_options)

    kw['fedmsg.consumers.ircbot.enabled'] = True

    from moksha.hub import main
    main(options=kw)
