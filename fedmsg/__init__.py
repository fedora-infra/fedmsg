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
""" Fedora Messaging Client API """

import threading

import fedmsg.core
import fedmsg.config

__local = threading.local()

__all__ = [
    'init',
    'send_message',
    'publish',
    'subscribe',
    'destroy',
    '__local',
]


def init(**kw):
    """ Initialize an instance of :class:`fedmsg.core.FedMsgContext`.

    The config is loaded with :func:`fedmsg.config.load_config` and updated
    by any keyword arguments.  This config is used to initialize the context
    object.

    The object is stored in a thread local as
    :data:`fedmsg.__local.__context`.
    """

    if getattr(__local, '__context', None):
        raise ValueError("fedmsg already initialized")

    # Read config from CLI args and a config file
    config = fedmsg.config.load_config([], None)

    # Override the defaults with whatever the user explicitly passes in.
    config.update(kw)

    __local.__context = fedmsg.core.FedMsgContext(**config)
    return __local.__context


def API_function(doc=None):
    def api_function(func):

        def _wrapper(*args, **kw):
            if not hasattr(__local, '__context'):
                init(**kw)
                assert(__local.__context)

            return func(*args, **kw)

        if not doc:
            _wrapper.__doc__ = func.__doc__
        else:
            _wrapper.__doc__ = doc

        _wrapper.__name__ = func.__name__
        return _wrapper

    return api_function


@API_function(doc=fedmsg.core.FedMsgContext.publish.__doc__)
def publish(topic=None, msg=None, **kw):
    return __local.__context.publish(topic, msg, **kw)

# This is old-school, and deprecated.
send_message = publish


@API_function(doc=fedmsg.core.FedMsgContext.destroy.__doc__)
def destroy(**kw):
    if hasattr(__local, '__context'):
        __local.__context.destroy()
        __local.__context = None


@API_function(doc=fedmsg.core.FedMsgContext.tail_messages.__doc__)
def tail_messages(**kw):
    for item in __local.__context.tail_messages(**kw):
        yield item
