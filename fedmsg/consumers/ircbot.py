# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Author: Ralph Bean
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels
import fedmsg
import fedmsg.json

import re
import pygments

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

        irc_settings = hub.config.get('irc')
        network = irc_settings.get('network', 'irc.freenode.net')
        port = irc_settings.get('port', 6667)
        channel = irc_settings.get('channel', None)
        if not channel:
            print "No channel specified"
            exit(1)
        channel = "#" + channel
        # TODO -- better default or no default at all
        nickname = irc_settings.get('nickname', "FedMsngr")

        self.filters = self.compile_filters(irc_settings.get('filters', None))

        factory = FedMsngrFactory(channel, nickname, self)
        reactor.connectTCP(network, port, factory)

        return super(IRCBotConsumer, self).__init__(hub)

    def add_irc_client(self, client):
        self.irc_clients.append(client)

    def del_irc_client(self, client):
        self.irc_clients.remove(client)

    def compile_filters(self, filters):
        compiled_filters = dict(
                topic=[],
                body=[]
                )

        for tag, flist in filters.items():
            for f in flist:
                compiled_filters[tag].append(re.compile(f))

        return compiled_filters

    def apply_filters(self, filters, topic, msg):
        for f in filters.get('topic', []):
            if f and re.search(f, topic):
                return False
        for f in filters.get('body', []):
            type(msg)
            if f and re.search(f, str(msg)):
                return False
        return True

    def prettify(self, msg):
        if self.hub.config.get('irc').get('make_pretty', True):
            fancy = pygments.highlight(
                    msg, pygments.lexers.JavascriptLexer(),
                    pygments.formatters.TerminalFormatter()
                    ).strip().encode('UTF-8')
            return fancy
        return msg

    def consume(self, msg):
        """ Forward on messages from the bus to all IRC connections. """
        for client in self.irc_clients:
            if client.factory.parent_consumer.filters:
                if self.apply_filters(client.factory.parent_consumer.filters, msg.get('topic'), msg.get('body')):
                    # apply all our message filters
                    if msg.get('body').get('topic'):
                        del(msg['body']['topic'])
                    client.msg(client.factory.channel, "Topic: %s\tMsg: %s" %
                                    (msg.pop('topic'),
                                        self.prettify(fedmsg.json.dumps(msg.get('body')))
                                    )
                                )
            else:
                client.msg(client.factory.channel, fedmsg.json.dumps(msg))
