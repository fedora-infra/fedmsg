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

from fedmsg.commands import BaseCommand
from fedmsg.consumers.relay import RelayConsumer

from kitchen.iterutils import iterate


class RelayCommand(BaseCommand):
    """ Relay connections from active loggers to the bus.

    ``fedmsg-relay`` is a service which binds to two ports, listens for
    messages on one and emits them on the other.  ``fedmsg-logger``
    requires that an instance of ``fedmsg-relay`` be running *somewhere*
    and that it's inbound address be listed in the config as one of the entries
    in :term:`relay_inbound`.

    ``fedmsg-relay`` becomes a necessity for integration points that cannot
    bind consistently to and serve from a port.  See :doc:`topology` for the
    mile-high view.  More specifically, ``fedmsg-relay`` is a
    SUB.bind()->PUB.bind() relay.
    """
    daemonizable = True
    name = 'fedmsg-relay'

    def run(self):
        # Do just like in fedmsg.commands.hub and mangle fedmsg.d/ to work
        # with moksha's expected configuration.
        moksha_options = dict(
            zmq_subscribe_endpoints=",".join(list(iterate(
                self.config['relay_inbound']
            ))),
            zmq_subscribe_method="bind",
        )
        self.config.update(moksha_options)

        # Flip the special bit that allows the RelayConsumer to run
        self.config[RelayConsumer.config_key] = True

        from moksha.hub import main
        for publish_endpoint in self.config['endpoints']['relay_outbound']:
            self.config['zmq_publish_endpoints'] = publish_endpoint
            try:
                return main(
                    # Pass in our config dict
                    options=self.config,
                    # Only run this *one* consumer
                    consumers=[RelayConsumer],
                    # Tell moksha to quiet its logging.
                    framework=False,
                )
            except zmq.ZMQError:
                self.log.debug("Failed to bind to %r" % publish_endpoint)

        raise IOError("Failed to bind to any outbound endpoints.")


def relay():
    command = RelayCommand()
    return command.execute()
