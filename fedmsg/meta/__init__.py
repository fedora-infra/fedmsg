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

import six

# gettext is used for internationalization.  I have tested that it can produce
# the correct files, but I haven't submitted it to anyone for translation.
import gettext
t = gettext.translation('fedmsg', 'locale', fallback=True)

if six.PY3:
    _ = t.gettext
else:
    _ = t.ugettext


from fedmsg.meta.default import DefaultProcessor
from fedmsg.meta.base import BaseConglomerator

import logging
log = logging.getLogger("fedmsg")


class ProcessorsNotInitialized(Exception):
    def __iter__(self):
        raise self
    __len__ = __iter__

    def __nonzero__(self):
        return False
    __bool__ = __nonzero__

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

    # If they're already initialized, then fine.
    if processors:
        return

    import pkg_resources
    processors = []
    for processor in pkg_resources.iter_entry_points('fedmsg.meta'):
        try:
            processors.append(processor.load()(_, **config))
        except Exception as e:
            log.warn("Failed to load %r processor." % processor.name)
            log.exception(e)

    # This should always be last
    processors.append(DefaultProcessor(_, **config))

    # By default we have three builtin processors:  Default, Logger, and
    # Announce.  If these are the only three, then we didn't find any
    # externally provided ones.  calls to msg2subtitle and msg2link likely will
    # not work the way the user is expecting.
    if len(processors) == 3:
        log.warn("No fedmsg.meta plugins found.  fedmsg.meta.msg2* crippled")


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


def conglomerate(messages, subject=None, lexers=False, **config):
    """ Return a list of messages with some of them grouped into conglomerate
    messages.  Conglomerate messages represent several other messages.

    For example, you might pass this function a list of 40 messages.
    38 of those are git.commit messages, 1 is a bodhi.update message, and 1 is
    a badge.award message.  This function could return a list of three
    messages, one representing the 38 git commit messages, one representing the
    bodhi.update message, and one representing the badge.award message.

    The ``subject`` argument is optional and will return "subjective"
    representations if possible (see msg2subjective(...)).

    Functionality is provided by fedmsg.meta plugins on a "best effort" basis.
    """

    # First, give every registered processor a chance to do its work
    for processor in processors:
        messages = processor.conglomerate(messages, subject=subject, **config)

    # Then, just fake it for every other ungrouped message.
    for i, message in enumerate(messages):
        # If these were successfully grouped, then skip
        if 'msg_ids' in message:
            continue

        # For ungrouped ones, replace them with a fake conglomerate
        messages[i] = BaseConglomerator.produce_template(
            [message], subject=subject, lexers=lexers, **config)
        # And fill out the fields that fully-implemented conglomerators would
        # normally fill out.
        messages[i].update({
            'link': msg2link(message, **config),
            'subtitle': msg2subtitle(message, **config),
            'subjective': msg2subjective(message, subject=subject, **config),
            'secondary_icon': msg2secondary_icon(message, **config),
        })

    return messages


@legacy_condition(six.text_type)
@with_processor()
def msg2repr(msg, processor, **config):
    """ Return a human-readable or "natural language" representation of a
    dict-like fedmsg message.  Think of this as the 'top-most level' function
    in this module.

    """
    fmt = u"{title} -- {subtitle} {link}"
    title = msg2title(msg, **config)
    subtitle = processor.subtitle(msg, **config)
    link = processor.link(msg, **config) or ''
    return fmt.format(**locals())


@legacy_condition(six.text_type)
@with_processor()
def msg2title(msg, processor, **config):
    """ Return a 'title' or primary text associated with a message. """
    return processor.title(msg, **config)


@legacy_condition(six.text_type)
@with_processor()
def msg2subtitle(msg, processor, **config):
    """ Return a 'subtitle' or secondary text associated with a message. """
    return processor.subtitle(msg, **config)


@legacy_condition(six.text_type)
@with_processor()
def msg2long_form(msg, processor, **config):
    """ Return a 'long form' text representation of a message.

    For most message, this will just default to the terse subtitle, but for
    some messages a long paragraph-structured block of text may be returned.
    """
    result = processor.long_form(msg, **config)
    if not result:
        result = processor.subtitle(msg, **config)
    return result


@with_processor()
def msg2lexer(msg, processor, **config):
    """ Return a Pygments lexer able to parse the long_form of this message.
    """
    return processor.lexer(msg, **config)


@legacy_condition(six.text_type)
@with_processor()
def msg2link(msg, processor, **config):
    """ Return a URL associated with a message. """
    return processor.link(msg, **config)


@legacy_condition(six.text_type)
@with_processor()
def msg2icon(msg, processor, **config):
    """ Return a primary icon associated with a message. """
    return processor.icon(msg, **config)


@legacy_condition(six.text_type)
@with_processor()
def msg2secondary_icon(msg, processor, **config):
    """ Return a secondary icon associated with a message. """
    return processor.secondary_icon(msg, **config)


@legacy_condition(set)
@with_processor()
def msg2usernames(msg, processor=None, legacy=False, **config):
    """ Return a set of FAS usernames associated with a message. """
    return processor.usernames(msg, **config)


@with_processor()
def msg2agent(msg, processor=None, legacy=False, **config):
    """ Return the single username who is the "agent" for an event.

    An "agent" is the one responsible for the event taking place, for example,
    if one person gives karma to another, then both usernames are returned by
    msg2usernames, but only the one who gave the karma is returned by
    msg2agent.

    If the processor registered to handle the message does not provide an
    agent method, then the *first* user returned by msg2usernames is returned
    (whether that is correct or not).  Here we assume that if a processor
    implements `agent`, then it knows what it is doing and we should trust
    that.  But if it does not implement it, we'll try our best guess.

    If there are no users returned by msg2usernames, then None is returned.
    """

    if not processor.agent is NotImplemented:
        return processor.agent(msg, **config)
    else:
        usernames = processor.usernames(msg, **config)
        # usernames is a set(), which doesn't support indexing.
        if usernames:
            return usernames.pop()

    # default to None if we can't find anything
    return None


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


@legacy_condition(six.text_type)
@with_processor()
def msg2subjective(msg, processor, subject, **config):
    """ Return a human-readable text representation of a dict-like
    fedmsg message from the subjective perspective of a user.

    For example, if the subject viewing the message is "oddshocks"
    and the message would normally translate into "oddshocks commented on
    ticket #174", it would instead translate into "you commented on ticket
    #174". """
    text = processor.subjective(msg, subject, **config)
    if not text:
        text = processor.subtitle(msg, **config)
    return text
