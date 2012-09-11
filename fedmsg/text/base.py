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

    Override handle_{title,subtitle,link} to use.
    """

    def __init__(self, internationalization_callable):
        self._ = internationalization_callable

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
