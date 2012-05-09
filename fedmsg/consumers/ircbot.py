# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Author: Ralph Bean
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels
import fedmsg
import fedmsg.json

from paste.deploy.converters import asbool
from moksha.api.hub.consumer import Consumer

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor

import logging
log = logging.getLogger("moksha.hub")


class FedMsngr(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        log.info("Signed on as %s." % (self.nickname,))

    def joined(self, channel):
        log.info("Joined %s." % (channel,))
        self.factory.parent_consumer.add_irc_client(self)

class FedMsngrFactory(protocol.ClientFactory):
    protocol = FedMsngr

    def __init__(self, channel, nickname, parent_consumer):
        self.channel = channel
        self.nickname = nickname
        self.parent_consumer = parent_consumer

    def clientConnectionLost(self, connector, reason):
        print "Lost connection (%s), reconnecting." % (reason,)
        self.parent_consumer.del_irc_client(connector)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Could not connect: %s" % (reason,)


class IRCBotConsumer(Consumer):
    topic = "org.fedoraproject.*"

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None
        self.irc_clients = []

        # Just for extracting config values.
        PREFIX = 'fedmsg.consumers.ircbot.'

        if not asbool(hub.config.get(PREFIX + 'enabled', False)):
            log.info('fedmsg.consumers.ircbot:IRCBotConsumer disabled.')
            return

        network = hub.config.get(PREFIX + 'network', 'irc.freenode.net')
        port = hub.config.get(PREFIX + 'port', 6667)
        # TODO -- better default or no default at all
        channel = hub.config.get(PREFIX + 'channel', "#fedmsg")
        # TODO -- better default or no default at all
        nickname = hub.config.get(PREFIX + 'nickname', "threebot")

        factory = FedMsngrFactory(channel, nickname, self)
        reactor.connectTCP(network, port, factory)

        return super(IRCBotConsumer, self).__init__(hub)

    def add_irc_client(self, client):
        self.irc_clients.append(client)

    def del_irc_client(self, client):
        self.irc_clients.remove(client)

    def consume(self, msg):
        """ Forward on messages from the bus to all IRC connections. """
        for client in self.irc_clients:
            client.msg(client.factory.channel, fedmsg.json.dumps(msg))
