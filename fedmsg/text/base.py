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


class BaseProcessor(object):
    """ Base Processor.  Without being extended, this doesn't actually handle
    any messages.

    Override handle_{title,subtitle,link,icon} to use.
    """

    # These five properties must be overridden by child-classes.
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

    def __init__(self, internationalization_callable):
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

    def handle_title(self, msg, **config):
        """ Return true if this processor can produce a "title" for this
        message.

        For this base class, this always returns ``False``.  Override it to
        return True in situations for which your :meth:`title` method can
        produce a title.
        """
        return False

    def title(self, msg, **config):
        """ Return a "title" for the message.

        This is only called if :meth:`handle_title` returned True.
        """
        raise NotImplementedError

    def handle_subtitle(self, msg, **config):
        """ Return true if this processor can produce a "subtitle" for this
        message.

        For this base class, this always returns ``False``.  Override it to
        return True in situations for which your :meth:`subtitle` method can
        produce a subtitle.
        """
        return False

    def subtitle(self, msg, **config):
        """ Return a "subtitle" for the message.

        This is only called if :meth:`handle_subtitle` returned True.
        """
        raise NotImplementedError

    def handle_link(self, msg, **config):
        """ Return true if this processor can produce a "link" for this
        message.

        For this base class, this always returns ``False``.  Override it to
        return True in situations for which your :meth:`link` method can
        produce a link.
        """
        return False

    def link(self, msg, **config):
        """ Return a "link" for the message.

        This is only called if :meth:`handle_link` returned True.
        """
        raise NotImplementedError

    def handle_icon(self, msg, **config):
        """ Return true if this processor can produce a "icon" for this
        message.

        For this base class, this always returns ``False``.  Override it to
        return True in situations for which your :meth:`icon` method can
        produce a icon.
        """
        return False

    def icon(self, msg, **config):
        """ Return a "icon" for the message.

        This is only called if :meth:`handle_icon` returned True.
        """
        raise NotImplementedError

    def handle_secondary_icon(self, msg, **config):
        """ Return true if this processor can produce a "secondary icon" for
        this message.

        For this base class, this always returns ``False``.  Override it to
        return True in situations for which your :meth:`icon` method can
        produce a icon.
        """
        return False

    def secondary_icon(self, msg, **config):
        """ Return a "secondary icon" for the message.

        This is only called if :meth:`handle_icon` returned True.
        """
        raise NotImplementedError
