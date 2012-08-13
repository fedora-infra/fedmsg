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
    if hasattr(__local, '__context'):
        raise ValueError("fedmsg already initialized")

    # Read config from CLI args and a config file
    config = fedmsg.config.load_config([], None)

    # Override the defaults with whatever the user explicitly passes in.
    config.update(kw)

    __local.__context = fedmsg.core.FedMsgContext(**config)
    return __local.__context


def API_function(func):

    def _wrapper(*args, **kw):
        if not hasattr(__local, '__context'):
            init(**kw)
            assert(__local.__context)

        return func(*args, **kw)
    return _wrapper


@API_function
def publish(topic=None, msg=None, **kw):
    """ Send a message over the publishing zeromq socket.

    Well, really it's a little more complicated:

     - If the zeromq context is not initialized, initialize it.
     - 'org.fedorahosted.' is prepended to the topic.

    FIXME - what if this is used in a webapp and the db transaction
    fails later on (during the commit)?  Then we will have sent this
    message to the bus without there really being a new tag in the DB.

    THOUGHT - We could solve this by putting all the hooks in
    sqlalchemy's post_commit dungeon.

    THOUGHT - We could have fedmsg intentionally defer the sending
    until after the next commit succeeds.  That way the 'call' still
    stays here in the controller (explicit == good).  This should be
    disablable, i.e. defer=False.

    >>> fedmsg.publish(topic='tag.create', tag.__json__())

    """

    return __local.__context.publish(topic, msg, **kw)

# This is old-school, and deprecated.
send_message = publish


@API_function
def subscribe(topic, callback, **kw):
    """ Subscribe a callback to a zeromq topic.

    Well, really it's a little more complicated:

     - If the zeromq context is not initialized, initialize it.
     - 'org.fedorahosted.' is prepended to the topic.
    """

    return __local.__context.subscribe(topic, callback)


@API_function
def destroy(**kw):
    """ Destroy a fedmsg context.

    You only need to call this if using fedmsg in a
    multi-threaded environment.
    """

    return __local.__context.destroy()


@API_function
def have_pulses(endpoints, **kw):
    """
    Returns a dict of endpoint->bool mappings indicating which endpoints
    are emitting detectable heartbeats.
    """

    return __local.__context.have_pulses(endpoints)
