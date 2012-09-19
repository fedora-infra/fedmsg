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
from fedmsg.consumers.relay import RelayConsumer

extra_args = []


@command(name="fedmsg-relay", extra_args=extra_args, daemonizable=True)
def relay(**kw):
    """ Relay connections from active loggers to the bus.

    ``fedmsg-relay`` is a service which binds to two ports, listens for
    messages on one and emits them on the other.  ``fedmsg-logger``
    requires that an instance of ``fedmsg-relay`` be running *somewhere*
    and that it's inbound address be listed in the config as
    :term:`relay_inbound`.

    ``fedmsg-relay`` becomes a necessity for integration points that cannot
    bind consistently to and serve from a port.  See :doc:`topology` for the
    mile-high view.  More specifically, ``fedmsg-relay`` is a
    SUB.bind()->PUB.bind() relay.
    """

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        zmq_publish_endpoints=",".join(kw['endpoints']["relay_outbound"]),
        zmq_subscribe_endpoints=kw['relay_inbound'],
        zmq_subscribe_method="bind",
    )
    kw.update(moksha_options)

    # Flip the special bit that allows the RelayConsumer to run
    kw[RelayConsumer.config_key] = True

    from moksha.hub import main
    main(options=kw, consumers=[RelayConsumer])
