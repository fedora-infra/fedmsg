# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
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
#           Luke Macken <lmacken@redhat.com>

import abc
import re
import time

import six


def add_metaclass(metaclass):
    """ Compat shim for el7. """
    if hasattr(six, 'add_metaclass'):
        return six.add_metaclass(metaclass)
    else:
        # Do nothing.  It's not worth it.
        return lambda klass: klass


class BaseProcessor(object):
    """ Base Processor.  Without being extended, this doesn't actually handle
    any messages.

    Processors require that an ``internationalization_callable`` be passed to
    them at instantiation.  Internationalization is often done at import time,
    but we handle it at runtime so that a single process may translate fedmsg
    messages into multiple languages.  Think: an IRC bot that runs
    #fedora-fedmsg, #fedora-fedmsg-es, #fedora-fedmsg-it.  Or: a twitter bot
    that posts to multiple language-specific accounts.

    That feature is currently unused, but fedmsg.meta supports future
    internationalization (there may be bugs to work out).

    """

    # These six properties must be overridden by child-classes.
    # They can be used by applications to give more context to messages.  If
    # the BodhiProcessor can handle a message, then our caller's code can use
    # these attributes to say "btw, this message is from Bodhi, the Fedora
    # update system.  It lives at https://admin.fedoraproject.org/updates/
    # and you can read more about it at https://fedoraproject.org/wiki/Bodhi"
    __name__ = None
    __description__ = None
    __link__ = None
    __docs__ = None
    __obj__ = None
    __icon__ = None

    # An automatically generated regex to match messages for this processor
    __prefix__ = None

    conglomerators = None
    topic_prefix_re = None

    def __init__(self, internationalization_callable, **config):
        self._ = internationalization_callable
        if not self.__name__:
            raise ValueError("Must declare a __name__")
        if not self.__description__:
            raise ValueError("Must declare a __description__")
        if not self.__link__:
            raise ValueError("Must declare a __link__")
        if not self.__docs__:
            raise ValueError("Must declare a __docs__")
        if not self.__obj__:
            raise ValueError("Must declare a __obj__")

        # Build a regular expression used to match message topics for us
        # A subclass may hardcode what topic prefix they are expecting (the
        # fedora plugin hardcodes fedora and the debian hardcodes debian).  For
        # backwards-compatibility reasons, if the subclassing plugin does not
        # hardcode a topic_prefix, then the global one is taken from config.
        if not self.topic_prefix_re:
            self.topic_prefix_re = config['topic_prefix_re']
        self.__prefix__ = re.compile('^%s\.(%s)(\.(.*))?$' % (
            self.topic_prefix_re, self.__name__.lower()))

        if self.conglomerators is None:
            self.conglomerators = []

        self.conglomerator_objects = []
        for i, conglomerator_class in enumerate(self.conglomerators):
            conglomerator = conglomerator_class(self, self._, **config)
            self.conglomerator_objects.append(conglomerator)

    def conglomerate(self, messages, **config):
        """ Given N messages, return another list that has some of them
        grouped together into a common 'item'.

        A conglomeration of messages should be of the following form::

          {
            'subtitle': 'relrod pushed commits to ghc and 487 other packages',
            'link': None,  # This could be something.
            'icon': 'https://that-git-logo',
            'secondary_icon': 'https://that-relrod-avatar',
            'start_time': some_timestamp,
            'end_time': some_other_timestamp,
            'human_time': '5 minutes ago',
            'usernames': ['relrod'],
            'packages': ['ghc', 'nethack', ... ],
            'topics': ['org.fedoraproject.prod.git.receive'],
            'categories': ['git'],
            'msg_ids': {
                '2014-abcde': {
                    'subtitle': 'relrod pushed some commits to ghc',
                    'title': 'git.receive',
                    'link': 'http://...',
                    'icon': 'http://...',
                },
                '2014-bcdef': {
                    'subtitle': 'relrod pushed some commits to nethack',
                    'title': 'git.receive',
                    'link': 'http://...',
                    'icon': 'http://...',
                },
            },
          }

        The telltale sign that an entry in a list of messages represents a
        conglomerate message is the presence of the plural ``msg_ids`` field.
        In contrast, ungrouped singular messages should bear a singular
        ``msg_id`` field.
        """
        for conglomerator in self.conglomerator_objects:
            messages = conglomerator.conglomerate(messages, **config)
        return messages

    def handle_msg(self, msg, **config):
        """
        If we can handle the given message, return the remainder of the topic.

        Returns None if we can't handle the message.
        """
        match = self.__prefix__.match(msg['topic'])
        if match:
            return match.groups()[-1] or ""

    def title(self, msg, **config):
        if not msg['topic'].startswith('/topic/'):
            return '.'.join(msg['topic'].split('.')[3:])
        return msg['topic']

    def subtitle(self, msg, **config):
        """ Return a "subtitle" for the message. """
        return ""

    def subjective(self, msg, subject, **config):
        """ Return a "subjective" subtitle for the message. """
        return ""

    def long_form(self, msg, **config):
        """ Return some paragraphs of text about a message. """
        return ""

    def lexer(self, msg, **config):
        """ Return a pygments lexer that can be applied to the long_form.

        Returns None if no lexer is associated.
        """
        return None

    def link(self, msg, **config):
        """ Return a "link" for the message. """
        return ""

    def icon(self, msg, **config):
        """ Return a "icon" for the message. """
        return self.__icon__

    def secondary_icon(self, msg, **config):
        """ Return a "secondary icon" for the message. """

    def usernames(self, msg, **config):
        """ Return a set of FAS usernames associated with a message. """
        return set()

    # XXX - this is intentionally not stubbed out at the 'base' level of the
    # class inheritance hierarchy.  In fedmsg/meta/__init__.py, we check for
    # the existance of this method on the subclass and do something special if
    # it is absent (if it is unimplemented by the subclass).
    agent = NotImplemented

    def packages(self, msg, **config):
        """ Return a set of package names associated with a message. """
        return set()

    def objects(self, msg, **config):
        """ Return a set of objects associated with a message. """
        return set()

    def emails(self, msg, **config):
        """ Return a dict of emails associated with a message. """
        return dict()

    def avatars(self, msg, **config):
        """ Return a dict of avatar URLs associated with a message. """
        return dict()


@add_metaclass(abc.ABCMeta)
class BaseConglomerator(object):
    """ Base Conglomerator.  This abstract base class must be extended.

    fedmsg.meta "conglomerators" are similar to but different from the
    fedmsg.meta "processors".  Where processors take a single message are
    return metadata about them (subtitle, a list of usernames, etc..),
    conglomerators take multiple messages and return a reduced subset of
    "conglomerate" messages.  Think: there are 100 messages where pbrobinson
    built 100 different packages in koji -- we can just represent those in a UI
    somewhere as a single message "pbrobinson built 100 different packages
    (click for details)".

    This BaseConglomerator is meant to be extended many times over to provide
    plugins that know how to conglomerate different combinations of messages.
    """
    def __init__(self, processor, internationalization_callable, **conf):
        self.processor = processor
        self._ = internationalization_callable

    def conglomerate(self, messages, subject=None, lexers=False, **conf):
        """ Top-level API entry point.  Given a list of messages, transform it
        into a list of conglomerates where possible.
        """
        indices, constituents = self.select_constituents(messages, **conf)
        while constituents:
            for idx in reversed(indices):
                messages.pop(idx)
            entry = self.merge(constituents, subject, lexers=lexers, **conf)
            messages.insert(idx, entry)
            indices, constituents = self.select_constituents(messages, **conf)

        return messages

    def skip(self, message, **config):
        # Skip ones that have already been squashed.
        if 'msg_ids' in message:
            return True
        # Skip ones we have no idea about
        if not self.can_handle(message, **config):
            return True
        return False

    def select_constituents(self, messages, **config):
        """ From a list of messages, return a subset that can be merged """
        for i, primary in enumerate(messages):
            if self.skip(primary, **config):
                continue

            # If we have one that looks good, find its siblings further down
            constituents = []
            base = i + 1
            for j, secondary in list(enumerate(messages))[base:]:
                if self.skip(secondary, **config):
                    continue
                if self.matches(primary, secondary, **config):
                    constituents.append((j, secondary))

            # If we found any, then return them and expect to be called afresh
            if constituents:
                return zip(*[(i, primary)] + constituents)

        # If we're done, we're done.
        return None, None

    @classmethod
    def produce_template(cls, constituents, subject, lexers=False, **config):
        """ Helper function used by `merge`.
        Produces the beginnings of a merged conglomerate message that needs to
        be later filled out by a subclass.
        """
        def _extract_timestamp(msg):
            value = msg['timestamp']
            if hasattr(value, 'timetuple'):
                value = time.mktime(value.timetuple())
            return value
        N = len(constituents)
        timestamps = [_extract_timestamp(msg) for msg in constituents]
        average_timestamp = sum(timestamps) / N

        # Avoid circular import
        import fedmsg.meta as fm
        # Optional, so, avoid importing it at the topmost level
        import arrow

        usernames = set(sum([
            list(fm.msg2usernames(msg, **config))
            for msg in constituents], []))
        packages = set(sum([
            list(fm.msg2packages(msg, **config))
            for msg in constituents], []))
        topics = set([msg['topic'] for msg in constituents])
        categories = set([t.split('.')[3] for t in topics])

        # Include metadata about constituent messages in the aggregate
        # http://da.gd/12Eso
        msg_ids = dict([
            (msg['msg_id'], {
                'title': fm.msg2title(msg, **config),
                'subtitle': fm.msg2subtitle(msg, **config),
                'subjective': fm.msg2subjective(msg, subject=subject, **config),
                'link': fm.msg2link(msg, **config),
                'icon': fm.msg2icon(msg, **config),
                '__icon__': getattr(fm.msg2processor(msg, **config), '__icon__', None),
                'secondary_icon': fm.msg2secondary_icon(msg, **config),
                'usernames': fm.msg2usernames(msg, **config),
                'packages': fm.msg2packages(msg, **config),
                'objects': fm.msg2objects(msg, **config),
                'long_form': fm.msg2long_form(msg, **config),
            }) for msg in constituents])

        # If the user asks for it, stuff in a pygments lexer too!
        if lexers:
            for msg in constituents:
                msg_ids[msg['msg_id']]['lexer'] = fm.msg2lexer(msg, **config)

        return {
            'start_time': min(timestamps),
            'end_time': max(timestamps),
            'timestamp': average_timestamp,
            'human_time': arrow.get(average_timestamp).humanize(),
            'msg_ids': msg_ids,
            'usernames': usernames,
            'packages': packages,
            'topics': topics,
            'categories': categories,
            'icon': fm.msg2icon(constituents[0], **config),
        }

    @staticmethod
    def list_to_series(items, N=3, oxford_comma=True):
        """ Convert a list of things into a comma-separated string.

        >>> list_to_series(['a', 'b', 'c', 'd'])
        'a, b, and 2 others'
        >>> list_to_series(['a', 'b', 'c', 'd'], N=4, oxford_comma=False)
        'a, b, c and d'

        """

        if not items:
            return "(nothing)"

        # uniqify items + sort them to have predictable (==testable) ordering
        items = list(sorted(set(items)))

        if len(items) == 1:
            return items[0]

        if len(items) > N:
            items[N - 1:] = ["%i others" % (len(items) - N + 1)]

        first = ", ".join(items[:-1])

        conjunction = " and "
        if oxford_comma and len(items) > 2:
            conjunction = "," + conjunction

        return first + conjunction + items[-1]

    @abc.abstractmethod
    def can_handle(self, msg, **config):
        """ Return true if we should begin to consider a given message. """
        pass

    @abc.abstractmethod
    def matches(self, a, b, **config):
        """ Return true if message a can be paired with message b. """
        pass

    @abc.abstractmethod
    def merge(self, constituents, subject, **config):
        """ Given N presumably matching messages, return one merged message """
        pass
