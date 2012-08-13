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
""" A SUB.bind()->PUB.bind() relay.

This works by flipping a special boolean in the config that enables
fedmsg.consumers.relay:RelayConsumer to run before starting up an
instance of the fedmsg-hub.

"""

import fedmsg
from fedmsg.commands import command
from fedmsg.consumers.relay import RelayConsumer
from fedmsg.producers.heartbeat import HeartbeatProducer

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
    main(options=kw, consumers=[RelayConsumer], producers=[HeartbeatProducer])
