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
# Author: Ralph Bean
# Description: A bot that takes a config and puts messages matching given
# regexes in specified IRC channels
import fedmsg
import fedmsg.encoding
import fedmsg.text

import copy
import re
import time
import pygments
import pygments.lexers
import pygments.formatters

from fedmsg.consumers import FedmsgConsumer

from twisted.words.protocols import irc
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import defer

import logging
log = logging.getLogger("moksha.hub")


mirc_colors = {
    "white": 0,
    "black": 1,
    "blue": 2,
    "green": 3,
    "red": 4,
    "brown": 5,
    "purple": 6,
    "orange": 7,
    "yellow": 8,
    "light green": 9,
    "teal": 10,
    "light cyan": 11,
    "light blue": 12,
    "pink": 13,
    "grey": 14,
    "light grey": 15,
}


def ircprettify(title, subtitle, link=""):
    def markup(s, color):
        return "\x03%i%s\x03" % (mirc_colors[color], s)

    if link:
        link = markup(link, "teal")

    color_lookup = {
        "fas": "light blue",
        "bodhi": "green",
        "git": "red",
        "tagger": "brown",
        "wiki": "purple",
        "logger": "orange",
    }
    title_color = color_lookup.get(title.split('.')[0], "light grey")
    title = markup(title, title_color)

    fmt = u"{title} -- {subtitle} {link}"
    return fmt.format(title=title, subtitle=subtitle, link=link)


class FedMsngr(irc.IRCClient):
    # The 0.6 seconds here is empircally guessed so we don't get dropped by
    # freenode.  FIXME - this should be pulled from the config.
    lineRate = 0.6
    sourceURL = "http://github.com/ralphbean/fedmsg"

    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def __init__(self, *args, **kwargs):
        self._modecallback = {}

    def signedOn(self):
        self.join(self.factory.channel)
        log.info("Signed on as %s." % (self.nickname,))

    def joined(self, channel):
        log.info("Joined %s." % (channel,))
        self.factory.parent_consumer.add_irc_client(self)

        def got_modes(modelist):
            modes = ''.join(modelist)
            if 'c' in modes:
                log.info("%s has +c is on. No prettiness" % channel)
                self.factory.pretty = False
        self.modes(channel).addCallback(got_modes)

    def modes(self, channel):
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._modecallback:
            self._modecallback[channel] = ([], [])
        self._modecallback[channel][0].append(d)
        self.sendLine("MODE %s" % channel)
        return d

    def irc_RPL_CHANNELMODEIS(self, prefix, params):
        """ Handy reference for IRC mnemonics
        www.irchelp.org/irchelp/rfc/chapter4.html#c4_2_3 """
        channel = params[1].lower()
        modes = params[2]
        if channel not in self._modecallback:
            return
        n = self._modecallback[channel][1]
        n.append(modes)
        callbacks, modelist = self._modecallback[channel]

        for cb in callbacks:
            cb.callback(modelist)
        del self._modecallback[channel]


class FedMsngrFactory(protocol.ClientFactory):
    protocol = FedMsngr

    def __init__(self, channel, nickname, filters,
                 pretty, terse, parent_consumer):
        self.channel = channel
        self.nickname = nickname
        self.filters = filters
        self.pretty = pretty
        self.terse = terse
        self.parent_consumer = parent_consumer

    def clientConnectionLost(self, connector, reason):
        log.warning("Lost connection (%s), reconnecting." % (reason,))
        self.parent_consumer.del_irc_clients(factory=self)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        log.error("Could not connect: %s" % (reason,))


class IRCBotConsumer(FedmsgConsumer):
    topic = "org.fedoraproject.*"
    validate_signatures = False
    config_key = 'fedmsg.consumers.ircbot.enabled'

    def __init__(self, hub):
        self.hub = hub
        self.DBSession = None
        self.irc_clients = []

        super(IRCBotConsumer, self).__init__(hub)

        if not getattr(self, '_initialized', False):
            return

        irc_settings = hub.config.get('irc')
        for settings in irc_settings:
            network = settings.get('network', 'irc.freenode.net')
            port = settings.get('port', 6667)
            channel = settings.get('channel', None)
            if not channel:
                log.error("No channel specified.  Ignoring entry.")
                continue

            if not channel.startswith("#"):
                channel = "#" + channel

            nickname = settings.get('nickname', "fedmsg-bot")
            pretty = settings.get('make_pretty', False)
            terse = settings.get('make_terse', False)
            timeout = settings.get('timeout', 120)

            filters = self.compile_filters(settings.get('filters', None))

            factory = FedMsngrFactory(channel, nickname, filters,
                                      pretty, terse, self)
            reactor.connectTCP(network, port, factory, timeout=timeout)

    def add_irc_client(self, client):
        self.irc_clients.append(client)

    def del_irc_clients(self, client=None, factory=None):
        if factory:
            self.irc_clients = [
                c for c in self.irc_clients
                if c.factory != factory
            ]

        if client and client in self.irc_clients:
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

    def prettify(self, topic, msg, pretty=False, terse=False):
        if terse:
            if pretty:
                return ircprettify(
                    title=fedmsg.text.msg2title(msg, **self.hub.config),
                    subtitle=fedmsg.text.msg2subtitle(msg, **self.hub.config),
                    link=fedmsg.text.msg2link(msg, **self.hub.config),
                )
            else:
                return fedmsg.text.msg2repr(msg, **self.hub.config)

        msg = copy.deepcopy(msg)

        if msg.get('topic', None):
            msg.pop('topic')

        if msg.get('timestamp', None):
            msg['timestamp'] = time.ctime(msg['timestamp'])

        if pretty:
            msg = pygments.highlight(
                    fedmsg.encoding.pretty_dumps(msg),
                    pygments.lexers.JavascriptLexer(),
                    pygments.formatters.TerminalFormatter()
                    ).strip().encode('UTF-8')

        return "{0:<30} {1}".format(topic, msg)

    def consume(self, msg):
        """ Forward on messages from the bus to all IRC connections. """
        topic, body = msg.get('topic'), msg.get('body')

        for client in self.irc_clients:
            if not client.factory.filters or (
                client.factory.filters and
                self.apply_filters(client.factory.filters, topic, body)
            ):
                raw_msg = self.prettify(
                    topic=topic,
                    msg=body,
                    pretty=client.factory.pretty,
                    terse=client.factory.terse,
                )
                raw_msg = raw_msg.encode('utf-8')
                client.msg(
                    client.factory.channel,
                    raw_msg,
                )
