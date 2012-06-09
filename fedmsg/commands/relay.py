""" A SUB.bind()->PUB.bind() relay.

This works by flipping a special boolean in the config that enables
fedmsg.consumers.relay:RelayConsumer to run before starting up an
instance of the fedmsg-hub.

"""

import fedmsg
from fedmsg.commands import command

extra_args = []


@command(name="fedmsg-relay", extra_args=extra_args, daemonizable=True)
def relay(**kw):
    """ Relay connections from active loggers to the bus. """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_publish_endpoints=",".join(kw['endpoints']["relay_outbound"]),
        zmq_subscribe_endpoints=kw['relay_inbound'],
        zmq_subscribe_method="bind",
    )
    kw.update(moksha_options)

    # Flip the special bit that allows the RelayConsumer to run
    kw['fedmsg.consumers.relay.enabled'] = True

    from moksha.hub import main
    main(options=kw)
