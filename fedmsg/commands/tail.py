import pprint

import fedmsg
from fedmsg.commands import command


extra_args = [
    (['--topic'], {
        'dest': 'topic',
        'help': 'The topic pattern to listen for.  Everything by default.',
        'default': '',
    }),
    (['--pretty'], {
        'dest': 'pretty_print',
        'help': 'Pretty print the JSON messages.',
        'default': False,
        'action': 'store_true',
    }),
]


@command(extra_args=extra_args)
def tail(**kw):
    """ Watch the bus. """

    # Disable sending
    kw['publish_endpoint'] = None
    # Disable timeouts.  We want to tail forever!
    kw['timeout'] = 0
    fedmsg.init(**kw)

    # Build a message formatter
    formatter = lambda s: s
    if kw['pretty_print']:
        formatter = lambda s: "\n" + pprint.pformat(s)

    # The "proper" fedmsg way to do this would be to spin up or connect to an
    # existing Moksha Hub and register a consumer on the "*" topic that simply
    # prints out each message it consumes.  That seems like overkill, so we're
    # just going to directly access the endpoints ourself.

    # TODO -- colors?
    # TODO -- tabular layout?
    for name, ep, topic, message in fedmsg.__context._tail_messages(**kw):
        if '_heartbeat' in topic:
            continue
        print name, ep, topic, formatter(message)
