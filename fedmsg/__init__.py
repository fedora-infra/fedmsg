""" Fedora Messaging Client API """

import fedmsg.core
import fedmsg.config

__all__ = [
    'init',
    'send_message',
    'publish',
    'subscribe',
]

__context = None


def init(**kw):

    global __context
    if __context:
        raise ValueError("fedmsg already initialized")

    # Read config from CLI args and a config file
    config = fedmsg.config.load_config([], None)

    # Override the defaults with whatever the user explicitly passes in.
    config.update(kw)

    __context = fedmsg.core.FedMsgContext(**config)
    return __context


def API_function(func):

    def _wrapper(*args, **kw):

        global __context
        if not __context:
            init(**kw)
            assert(__context)

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

    return __context.publish(topic, msg, **kw)

# This is old-school, and deprecated.
send_message = publish

@API_function
def subscribe(topic, callback, **kw):
    """ Subscribe a callback to a zeromq topic.

    Well, really it's a little more complicated:

     - If the zeromq context is not initialized, initialize it.
     - 'org.fedorahosted.' is prepended to the topic.
    """

    return __context.subscribe(topic, callback)


@API_function
def have_pulses(endpoints, **kw):
    """
    Returns a dict of endpoint->bool mappings indicating which endpoints
    are emitting detectable heartbeats.
    """

    return __context.have_pulses(endpoints)
