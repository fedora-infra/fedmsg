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
""" :mod:`fedmsg.text` handles the conversion of fedmsg messages
(dict-like json objects) into internationalized human-readable
strings:  strings like ``"nirik voted on a tag in tagger"`` and
``"lmacken commented on a bodhi update."``

The intent is to use the module 1) in the ``fedmsg-irc`` bot and 2) in the
gnome-shell desktop notification widget.  The sky is the limit, though.

The primary entry point is :func:`fedmsg.text.msg2repr` which takes a dict and
returns the string representation.  Portions of that string are in turn
produced by :func:`fedmsg.text._msg2title`, :func:`fedmsg.text._msg2subtitle`,
and :func:`fedmsg.text._msg2link`.

Message processing is handled by a list of MessageProcessors (instances of
:class:`fedmsg.text.base.BaseProcessor`) which defined in
submodules of this module.  Messages for which no MessageProcessor exists are
handled gracefully.

If you'd like to add a new processor, you'll need to extend
:class:`fedmsg.text.base.BaseProcessor` and override the appropriate methods.
Your new class will need to be added to the :data:`fedmsg.text.processors` list
to be used.

"""

# gettext is used for internationalization.  I have tested that it can produce
# the correct files, but I haven't submitted it to anyone for translation.
import gettext
t = gettext.translation('fedmsg', 'locale', fallback=True)
_ = t.ugettext

import fedmsg.crypto

from fedmsg.text.bodhi import BodhiProcessor
from fedmsg.text.scm import SCMProcessor
from fedmsg.text.tagger import TaggerProcessor
from fedmsg.text.supybot import SupybotProcessor
from fedmsg.text.mediawiki import WikiProcessor
from fedmsg.text.fas import FASProcessor
from fedmsg.text.compose import ComposeProcessor
from fedmsg.text.logger import LoggerProcessor
from fedmsg.text.default import DefaultProcessor

processors = [
    BodhiProcessor(_),
    SCMProcessor(_),
    TaggerProcessor(_),
    SupybotProcessor(_),
    WikiProcessor(_),
    FASProcessor(_),
    ComposeProcessor(_),
    LoggerProcessor(_),
    DefaultProcessor(_),
]


def msg2repr(msg, **config):
    """ Return a human-readable or "natural language" representation of a
    dict-like fedmsg message.

    """

    fmt = u"{title} -- {subtitle} {link}"
    title = _msg2title(msg, **config)
    subtitle = _msg2subtitle(msg, **config)
    link = _msg2link(msg, **config)
    return fmt.format(**locals())


def _msg2title(msg, **config):
    for p in processors:
        if not p.handle_title(msg, **config):
            continue
        title = p.title(msg, **config)
        break

    suffix = _msg2suffix(msg, **config)
    if suffix:
        title = title + " " + suffix

    return title


def _msg2subtitle(msg, **config):
    for p in processors:
        if not p.handle_subtitle(msg, **config):
            continue
        return p.subtitle(msg, **config)

    # This should never happen.
    # DefaultProcessor should always catch messages.
    raise RuntimeError("No text processor caught the message.")


def _msg2link(msg, **config):
    for p in processors:
        if not p.handle_link(msg, **config):
            continue
        return p.link(msg, **config)

    # This should never happen.
    # DefaultProcessor should always catch messages.
    raise RuntimeError("No text processor caught the message.")


def _msg2icon(msg, **config):
    for p in processors:
        if not p.handle_icon(msg, **config):
            continue
        return p.icon(msg, **config)

    # This should never happen.
    # DefaultProcessor should always catch messages.
    raise RuntimeError("No text processor caught the message.")


def _msg2suffix(msg, **config):
    if 'signature' not in msg:
        return _("(unsigned)")
    elif config.get('validate_signatures'):
        if not fedmsg.crypto.validate(msg, **config):
            return _("(invalid signature!)")

    return ""
