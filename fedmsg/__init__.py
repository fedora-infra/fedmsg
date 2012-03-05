""" Fedora Messaging Client API """

import fedmsg.core

__all__ = [
    'init',
    'send_message',
    'subscribe',
]

__context = None


def init(**kw):
    global __context
    if __context:
        raise ValueError("fedmsg already initialized")

    __context = fedmsg.core.FedMsgContext(**kw)
    return __context


def send_message(topic, msg, **kw):
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

    >>> fedmsg.send_message(topic='tag.new', tag.__json__())

    """

    global __context
    if not __context:
        init()
        assert(__context)

    return __context.send_message(topic, msg, **kw)


def subscribe(topic, callback, **kw):
    """ Subscribe a callback to a zeromq topic.

    Well, really it's a little more complicated:

     - If the zeromq context is not initialized, initialize it.
     - 'org.fedorahosted.' is prepended to the topic.
    """

    global __context
    if not __context:
        init()
        assert(__context)

    return __context.subscribe(topic, callback, **kw)
