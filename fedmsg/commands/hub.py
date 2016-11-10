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
from gettext import gettext as _
import resource

from fedmsg.utils import load_class
from fedmsg.commands import BaseCommand


# Since many services use fedmsg-hubs, processes can exceed their resource
# limits on the number of open file descriptors. In the long term, apps should
# stop listening to every service, but as a short term fix an attempt is made
# to raise the resource limit here.
MAX_NOFILE = 4096


class HubCommand(BaseCommand):
    """ Run the fedmsg hub.

    ``fedmsg-hub`` is the all-purpose daemon.  This should be run on every host
    that has services which declare their own consumers.  ``fedmsg-hub`` will
    listen to every endpoint discovered by :mod:`fedmsg.config` and forward
    messages in-process to the locally-declared consumers.  It is a thin
    wrapper over a moksha-hub.

    Other commands like ``fedmsg-irc`` are just specialized, restricted
    versions of ``fedmsg-hub``.  ``fedmsg-hub`` is the most general/abstract.

    ``fedmsg-hub`` also houses the functions to run a websocket server.

    """
    name = 'fedmsg-hub'
    daemonizable = True
    extra_args = [
        (['--with-consumers'], {
            'dest': 'explicit_hub_consumers',
            'type': str,
            'help': 'A comma-delimited list of conumers to run.',
            'default': None,
        }),
        (['--websocket-server-port'], {
            'dest': 'moksha.livesocket.websocket.port',
            'type': int,
            'help': 'Port on which to host the websocket server.',
            'default': None,
        }),
    ]

    def run(self):
        # Check if the user wants the websocket server to run
        if self.config['moksha.livesocket.websocket.port']:
            self.config['moksha.livesocket.backend'] = 'websocket'

        # If the user wants to override any consumers installed on the system
        # and *only* run the ones they want to, they can do that.
        consumers = None
        if self.config['explicit_hub_consumers']:
            locations = self.config['explicit_hub_consumers'].split(',')
            locations = [load_class(location) for location in locations]

        # Rephrase the fedmsg-config.py config as moksha *.ini format for
        # zeromq. If we're not using zeromq (say, we're using STOMP), then just
        # assume that the moksha configuration is specified correctly already
        # in /etc/fedmsg.d/
        if self.config.get('zmq_enabled', True):
            moksha_options = dict(
                zmq_subscribe_endpoints=','.join(
                    ','.join(bunch) for bunch in self.config['endpoints'].values()
                ),
            )
            self.config.update(moksha_options)

        self.set_rlimit_nofiles()

        # Note that the hub we kick off here cannot send any message.  You
        # should use fedmsg.publish(...) still for that.
        from moksha.hub import main
        main(
            # Pass in our config dict
            options=self.config,
            # Only run the specified consumers if any are so specified.
            consumers=consumers,
            # Tell moksha to quiet its logging.
            framework=False,
        )

    def set_rlimit_nofiles(self, limit=MAX_NOFILE):
        try:
            msg = _(u'Setting RLIMIT_NOFILE to '
                    u'{max_files}').format(max_files=limit)
            self.log.info(msg)
            resource.setrlimit(
                resource.RLIMIT_NOFILE, (limit, limit))
        except (resource.error, ValueError) as e:
            msg = _(u'Failed to raise the limit on the maximum number of open '
                    u'file descriptors to {max_files}: {err}')
            self.log.warning(msg.format(max_files=limit, err=str(e)))
        finally:
            nofile = resource.getrlimit(resource.RLIMIT_NOFILE)
            self.log.info(
                _(u'RLIMIT_NOFILE is set to {nofile}').format(nofile=nofile))


def hub():
    command = HubCommand()
    command.execute()
