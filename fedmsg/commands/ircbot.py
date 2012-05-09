#!/usr/bin/env python
# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels

from twisted.words.protocols import irc
from twisted.internet import protocol


class FedMsngr(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % (self.nickname,)

    def joined(self, channel):
        print "Joined %s." % (channel,)

    def privmsg(self, user, channel, msg):
        if not user:
            return
        if self.nickname in msg:
            prefix = user.split('!', 1)[0] + ": "
        else:
            prefix = ''
        self.msg(self.factory.channel, prefix + "Reply!")

    def consume(self, message):
        self.msg(self.factory.channel, message)


class FedMsngrFactory(protocol.ClientFactory):
    protocol = FedMsngr

    def __init__(self, channel, nickname='FedMsngr'):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)

#import sys
#from twisted.internet import reactor

#if __name__ == "__main__":
    #chan = sys.argv[1]
    #reactor.connectTCP('irc.freenode.net', 6667, FedMsngrFactory('#' + chan))
    #reactor.run()


######################################################################
from fedmsg.commands import command

extra_args = [
    (['--channel'], {
        'dest': 'channel',
        'help': "The channel to join",
    }),
]


@command(extra_args=extra_args)
def relay(**kw):
    """ Relay connections from active loggers to the bus. """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_subscribe_endpoints=kw['endpoints']['relay_outbound'],
        zmq_subscribe_method="bind",
    )
    kw.update(moksha_options)

    from moksha.hub import main
    from twisted.internet import reactor
    reactor.connectTCP('irc.freenode.net', 6667, FedMsngrFactory('#' + kw['channel']))
    main(options=kw)
