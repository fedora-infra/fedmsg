# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels.  See fedmsg-config.py for options.
from fedmsg.commands import command

from fedmsg.consumers.ircbot import IRCBotConsumer
from fedmsg.producers.heartbeat import HeartbeatProducer

extra_args = []


@command(name="fedmsg-irc", extra_args=extra_args, daemonizable=True)
def ircbot(**kw):
    """ Relay connections from active loggers to the bus. """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_subscribe_endpoints=','.join(
            ','.join(bunch) for bunch in kw['endpoints'].values()
        ),
    )
    kw.update(moksha_options)

    kw['fedmsg.consumers.ircbot.enabled'] = True

    from moksha.hub import main
    main(options=kw, consumers=[IRCBotConsumer], producers=[HeartbeatProducer])
