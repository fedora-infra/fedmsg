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
"""
"""

import fedmsg
from fedmsg.commands import command
from fedmsg.consumers.gateway import GatewayConsumer

extra_args = []


@command(name="fedmsg-gateway", extra_args=extra_args, daemonizable=True)
def gateway(**kw):
    """ Rebroadcast messages to a special zmq endpoint.

    A repeater that rebroadcasts all messages received to a special zmq
    endpoint.  This is used to get messages from inside Fedora Infrastructure
    out to users.  Its communication is uni-directional.  It does not relay
    messages from "outside the bus" back in.

    The special zmq endpoint is specified by the presence of
    :term:`fedmsg.consumers.gateway.port` in the config.

    This service is what makes using ":doc:`consuming`" outside the
    VPN/firewalled bus environment possible.
    """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_subscribe_endpoints=','.join(
            ','.join(bunch) for bunch in
            kw['endpoints'].values()
        ),
    )
    kw.update(moksha_options)

    # Flip the special bit that allows the GatewayConsumer to run
    kw[GatewayConsumer.config_key] = True

    from moksha.hub import main
    main(options=kw, consumers=[GatewayConsumer])
