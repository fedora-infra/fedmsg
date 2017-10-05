# This file is part of fedmsg.
# Copyright (C) 2017 Red Hat, Inc.
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
# Authors: Jeremy Cline <jeremy@jcline.org>
"""
The ``fedmsg-check`` command can be used to see what fedmsg consumers and
producers are currently active. It requires that the ``moksha.monitoring.socket``
is defined in the fedmsg configuration.
"""
from gettext import gettext as _
import json

import click
import zmq

from fedmsg.config import load_config


TIMEOUT_HELP = _("The number of seconds to wait for a heartbeat from the fedmsg hub."
                 " The default is 10 seconds.")
CONSUMER_HELP = _("The name of the consumer to check the status of.")
PRODUCER_HELP = _("The name of the producer to check the status of.")


@click.command()
@click.option('--timeout', default=10, type=click.INT, help=TIMEOUT_HELP)
@click.option('--consumer', '-c', multiple=True, help=CONSUMER_HELP)
@click.option('--producer', '-p', multiple=True, help=PRODUCER_HELP)
def check(timeout, consumer=None, producer=None):
    """This command is used to check the status of consumers and producers.

    If no consumers and producers are provided, the status of all consumers and producers
    is printed.
    """
    # It's weird to say --consumers, but there are multiple, so rename the variables
    consumers, producers = consumer, producer

    config = load_config()
    endpoint = config.get('moksha.monitoring.socket')
    if not endpoint:
        raise click.ClickException('No monitoring endpoint has been configured: '
                                   'please set "moksha.monitoring.socket"')

    context = zmq.Context.instance()
    socket = context.socket(zmq.SUB)
    # ZMQ takes the timeout in milliseconds
    socket.set(zmq.RCVTIMEO, timeout * 1000)
    socket.subscribe(b'')
    socket.connect(endpoint)

    try:
        message = socket.recv_json()
    except zmq.error.Again:
        raise click.ClickException(
            'Failed to receive message from the monitoring endpoint ({e}) in {t} '
            'seconds.'.format(e=endpoint, t=timeout))

    if not consumers and not producers:
        click.echo('No consumers or producers specified so all will be shown.')
    else:
        missing = False
        uninitialized = False
        for messager_type, messagers in (('consumers', consumers), ('producers', producers)):
            active = {}
            for messager in message[messager_type]:
                active[messager['name']] = messager
            for messager in messagers:
                if messager not in active:
                    click.echo('"{m}" is not active!'.format(m=messager), err=True)
                    missing = True
                else:
                    if active[messager]['initialized'] is not True:
                        click.echo('"{m}" is not initialized!'.format(m=messager), err=True)
                        uninitialized = True

        if missing:
            raise click.ClickException('Some consumers and/or producers are missing!')
        elif uninitialized:
            raise click.ClickException('Some consumers and/or producers are uninitialized!')
        else:
            click.echo('All consumers and producers are active!')

    click.echo(json.dumps(message, indent=2, sort_keys=True))
