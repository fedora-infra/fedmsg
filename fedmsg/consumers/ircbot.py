# -*- coding; utf-8 -*-
# Author: Ryan Brown
# Author: Ralph Bean
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels
import fedmsg
import fedmsg.json

import re
import pygments
import pygments.lexers
import pygments.formatters

from paste.deploy.converters import asbool
from moksha.api.hub.consumer import Consumer

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor

import logging
log = logging.getLogger("moksha.hub")


class FedMsngr(irc.IRCClient):
    lineRate = None
    sourceURL = "http://github.com/ralphbean/fedmsg"

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

    def __init__(self, channel, nickname, filters, pretty, parent_consumer):
        self.channel = channel
        self.nickname = nickname
        self.filters = filters
        self.pretty = pretty
        self.parent_consumer = parent_consumer

    def clientConnectionLost(self, connector, reason):
        log.warning("Lost connection (%s), reconnecting." % (reason,))
        self.parent_consumer.del_irc_client(connector)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        log.error("Could not connect: %s" % (reason,))


class IRCBotConsumer(Consumer):
    topic = "org.fedoraproject.*"

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None
        self.irc_clients = []

        ENABLED = 'fedmsg.consumers.ircbot.enabled'
        if not asbool(hub.config.get(ENABLED, False)):
            log.info('fedmsg.consumers.ircbot:IRCBotConsumer disabled.')
            return

        irc_settings = hub.config.get('irc')
        for settings in irc_settings:
            network = settings.get('network', 'irc.freenode.net')
            port = settings.get('port', 6667)
            channel = settings.get('channel', None)
            if not channel:
                log.error("No channel specified")
                exit(1)
            channel = "#" + channel
            nickname = settings.get('nickname', "fedmsg-bot")
            pretty = settings.get('make_pretty', False)

            filters = self.compile_filters(settings.get('filters', None))

            factory = FedMsngrFactory(channel, nickname, filters, pretty, self)
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

    def prettify(self, msg, pretty=False):
        if pretty:
            fancy = pygments.highlight(
                    msg, pygments.lexers.JavascriptLexer(),
                    pygments.formatters.TerminalFormatter()
                    ).strip().encode('UTF-8')
            return fancy
        return msg

    def consume(self, msg):
        """ Forward on messages from the bus to all IRC connections. """
        topic, body = msg.get('topic'), msg.get('body')
        for client in self.irc_clients:
            if client.factory.filters:
                if self.apply_filters(client.factory.filters, topic, body):
                    _body = self.prettify(
                        fedmsg.json.dumps(body),
                        pretty=client.factory.pretty
                    )
                    client.msg(
                        client.factory.channel,
                        "{0:<30} {1}".format(topic, _body),
                    )
            else:
                client.msg(
                    client.factory.channel,
                    fedmsg.json.dumps(msg),
                )
