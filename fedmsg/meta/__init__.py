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
#
""" :mod:`fedmsg.meta` handles the conversion of fedmsg messages
(dict-like json objects) into internationalized human-readable
strings:  strings like ``"nirik voted on a tag in tagger"`` and
``"lmacken commented on a bodhi update."``

The intent is to use the module 1) in the ``fedmsg-irc`` bot and 2) in the
gnome-shell desktop notification widget.  The sky is the limit, though.

The primary entry point is :func:`fedmsg.meta.msg2repr` which takes a dict and
returns the string representation.  Portions of that string are in turn
produced by :func:`fedmsg.meta.msg2title`, :func:`fedmsg.meta.msg2subtitle`,
and :func:`fedmsg.meta.msg2link`.

Message processing is handled by a list of MessageProcessors (instances of
:class:`fedmsg.meta.base.BaseProcessor`) which are discovered on a setuptools
**entry-point**.  Messages for which no MessageProcessor exists are
handled gracefully.

The original deployment of fedmsg in `Fedora Infrastructure` uses metadata
providers/message processors from a plugin called
`fedmsg_meta_fedora_infrastructure
<https://github.com/fedora-infra/fedmsg_meta_fedora_infrastructure>`_.
If you'd like to add your own processors for your own deployment, you'll need
to extend :class:`fedmsg.meta.base.BaseProcessor` and override the appropriate
methods.  If you package up your processor and expose it on the ``fedmsg.meta``
entry-point, your new class will need to be added to the
:data:`fedmsg.meta.processors` list at runtime.

End users can have multiple plugin sets installed simultaneously.

"""

# gettext is used for internationalization.  I have tested that it can produce
# the correct files, but I haven't submitted it to anyone for translation.
import gettext
t = gettext.translation('fedmsg', 'locale', fallback=True)
_ = t.ugettext

from fedmsg.meta.default import DefaultProcessor

import pkg_resources
import logging


class ProcessorsNotInitialized(Exception):
    def __iter__(self):
        raise self
    __len__ = __iter__

processors = ProcessorsNotInitialized("You must first call "
                                      "fedmsg.meta.make_processors(**config)")


def make_processors(**config):
    """ Initialize all of the text processors.

    You'll need to call this once before using any of the other functions in
    this module.

        >>> import fedmsg.config
        >>> import fedmsg.meta
        >>> config = fedmsg.config.load_config([], None)
        >>> fedmsg.meta.make_processors(**config)
        >>> text = fedmsg.meta.msg2repr(some_message_dict, **config)

    """
    global processors
    processors = []
    for processor in pkg_resources.iter_entry_points('fedmsg.meta'):
        try:
            processors.append(processor.load()(_, **config))
        except Exception as e:
            log = logging.getLogger("fedmsg")
            log.warn("Failed to load %r processor." % processor.name)
            log.warn(str(e))

    # This should always be last
    processors.append(DefaultProcessor(_, **config))


def msg2processor(msg, **config):
    """ For a given message return the text processor that can handle it.

    This will raise a :class:`fedmsg.meta.ProcessorsNotInitialized` exception
    if :func:`fedmsg.meta.make_processors` hasn't been called yet.
    """
    for processor in processors:
        if processor.handle_msg(msg, **config) is not None:
            return processor
    else:
        return processors[-1]  # DefaultProcessor


def legacy_condition(cls):
    def _wrapper(f):
        def __wrapper(msg, legacy=False, **config):
            try:
                return f(msg, **config)
            except KeyError:
                if legacy:
                    return cls()
                else:
                    raise

        __wrapper.__doc__ = f.__doc__
        __wrapper.__name__ = f.__name__
        return __wrapper
    return _wrapper


def with_processor():
    def _wrapper(f):
        def __wrapper(msg, processor=None, **config):
            if not processor:
                processor = msg2processor(msg, **config)

            return f(msg, processor=processor, **config)

        __wrapper.__doc__ = f.__doc__
        __wrapper.__name__ = f.__name__
        return __wrapper
    return _wrapper


@legacy_condition(unicode)
@with_processor()
def msg2repr(msg, processor, **config):
    """ Return a human-readable or "natural language" representation of a
    dict-like fedmsg message.  Think of this as the 'top-most level' function
    in this module.

    """
    fmt = u"{title} -- {subtitle} {link}"
    title = msg2title(msg, **config)
    subtitle = processor.subtitle(msg, **config)
    link = processor.link(msg, **config)
    return fmt.format(**locals())


@legacy_condition(unicode)
@with_processor()
def msg2title(msg, processor, **config):
    """ Return a 'title' or primary text associated with a message. """
    return processor.title(msg, **config)


@legacy_condition(unicode)
@with_processor()
def msg2subtitle(msg, processor, **config):
    """ Return a 'subtitle' or secondary text associated with a message. """
    return processor.subtitle(msg, **config)


@legacy_condition(unicode)
@with_processor()
def msg2link(msg, processor, **config):
    """ Return a URL associated with a message. """
    return processor.link(msg, **config)


@legacy_condition(unicode)
@with_processor()
def msg2icon(msg, processor, **config):
    """ Return a primary icon associated with a message. """
    return processor.icon(msg, **config)


@legacy_condition(unicode)
@with_processor()
def msg2secondary_icon(msg, processor, **config):
    """ Return a secondary icon associated with a message. """
    return processor.secondary_icon(msg, **config)


@legacy_condition(set)
@with_processor()
def msg2usernames(msg, processor=None, legacy=False, **config):
    """ Return a set of FAS usernames associated with a message. """
    return processor.usernames(msg, **config)


@legacy_condition(set)
@with_processor()
def msg2packages(msg, processor, **config):
    """ Return a set of package names associated with a message. """
    return processor.packages(msg, **config)


@legacy_condition(set)
@with_processor()
def msg2objects(msg, processor, **config):
    """ Return a set of objects associated with a message.

    "objects" here is the "objects" from english grammar.. meaning, the thing
    in the message upon which action is being done.  The "subject" is the
    user and the "object" is the packages, or the wiki articles, or the blog
    posts.

    Where possible, use slash-delimited names for objects (as in wiki URLs).
    """
    return processor.objects(msg, **config)


@legacy_condition(dict)
@with_processor()
def msg2emails(msg, processor, **config):
    """ Return a dict mapping of usernames to email addresses. """
    return processor.emails(msg, **config)


@legacy_condition(dict)
@with_processor()
def msg2avatars(msg, processor, **config):
    """ Return a dict mapping of usernames to avatar URLs. """
    return processor.avatars(msg, **config)
