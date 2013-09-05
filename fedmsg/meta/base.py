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
#           Luke Macken <lmacken@redhat.com>

import re


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
    # and you can read more about it at http://fedoraproject.org/wiki/Bodhi"
    __name__ = None
    __description__ = None
    __link__ = None
    __docs__ = None
    __obj__ = None
    __icon__ = None

    # An automatically generated regex to match messages for this processor
    __prefix__ = None

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
        self.__prefix__ = re.compile('^%s\.(%s)\.?(.*)$' % (
            config['topic_prefix_re'], self.__name__.lower()))

    def handle_msg(self, msg, **config):
        """
        If we can handle the given message, return the remainder of the topic.
        """
        match = self.__prefix__.match(msg['topic'])
        if match:
            return match.groups()[-1]

    def title(self, msg, **config):
        return '.'.join(msg['topic'].split('.')[3:])

    def subtitle(self, msg, **config):
        """ Return a "subtitle" for the message. """
        return ""

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
