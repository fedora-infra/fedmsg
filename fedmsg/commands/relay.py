""" A SUB.bind()->PUB.bind() relay. """

import fedmsg
from fedmsg.commands import command

extra_args = []


# FIXME, @command needs a 'minus_args' argument to disable topic-prefix here.
@command(extra_args=extra_args)
def relay(**kw):
    """ Relay connections from active loggers to the bus. """

    # Configure ourselves to send message out our outbound endpoint
    fedmsg.init(name='relay_outbound', **kw)

    # Tail messages from our passive listening endpoint
    kw['endpoints'] = dict(relay_inbound=kw['relay_inbound'])
    kw['passive'] = True
    kw['timeout'] = 0

    # n, e, t, m -> name, endpoint, topic, message
    for n, e, t, m in fedmsg.__context._tail_messages(**kw):
        #print "Forwarding %r from %r." % (t, e)
        fedmsg.__context.publisher.send_multipart([t, fedmsg.json.dumps(m)])
