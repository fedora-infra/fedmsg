""" A SUB.bind()->PUB.bind() relay. """

import fedmsg
from fedmsg.commands import command

extra_args = [
    (['--listen'], {
        'dest': 'relay',
        'help': "Endpoint to listen for new connections on.",
        'default': "tcp://127.0.0.1:3002",
    }),
    (['--send'], {
        'dest': 'publish_endpoint',
        'help': "Endpoint to re-publish messages to.",
        'default': "tcp://127.0.0.1:6543",
    }),
]


# FIXME, @command needs a 'minus_args' argument to disable topic-prefix here.
@command(extra_args=extra_args)
def relay(**kw):
    """ Relay connections from active loggers to the bus. """

    # Tail messages from our passive listening endpoint
    kw['passive'] = True
    kw['timeout'] = 0
    kw['endpoints'] = [kw['relay']]

    fedmsg.init(**kw)

    # e, t, m -> endpoint, topic, message
    for e, t, m in fedmsg.__context._tail_messages(**kw):
        #print "Forwarding %r from %r to %r." % (t, e, kw['publish_endpoint'])
        fedmsg.__context.publisher.send_multipart([t, fedmsg.json.dumps(m)])
