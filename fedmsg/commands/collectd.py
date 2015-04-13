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
import datetime
import socket
import time

import fedmsg
import fedmsg.meta

from fedmsg.commands import BaseCommand
from fedmsg.consumers import FedmsgConsumer
from moksha.hub.api import PollingProducer


class CollectdConsumer(FedmsgConsumer):
    config_key = "fedmsg.commands.collectd.enabled"
    validate_messages = False
    topic = '*'

    def __init__(self, hub):
        self.hub = hub

        super(CollectdConsumer, self).__init__(hub)
        self._dict = dict([
            (p.__name__.lower(), 0) for p in fedmsg.meta.processors
        ])
        self.host = socket.gethostname().split('.')[0]

    def consume(self, msg):
        processor = fedmsg.meta.msg2processor(msg, **self.hub.config)
        modname = processor.__name__.lower()
        self._dict[modname] += 1

    def dump(self):
        """ Called by CollectdProducer every `n` seconds. """

        # Print out the collectd feedback.
        # This is sent to stdout while other log messages are sent to stderr.
        for k, v in sorted(self._dict.items()):
            print(self.formatter(k, v))

        # Reset each entry to zero
        for k, v in sorted(self._dict.items()):
            self._dict[k] = 0

    def formatter(self, key, value):
        """ Format messages for collectd to consume. """
        template = "PUTVAL {host}/fedmsg/fedmsg_wallboard-{key} " +\
            "interval={interval} {timestamp}:{value}"
        timestamp = int(time.time())
        interval = self.hub.config['collectd_interval']
        return template.format(
            host=self.host,
            timestamp=timestamp,
            value=value,
            interval=interval,
            key=key,
        )


class CollectdProducer(PollingProducer):
    # "Frequency" is set later at runtime.
    def poll(self):
        self.hub.consumers[0].dump()


class CollectdCommand(BaseCommand):
    """ Print machine-readable information for collectd to monitor the bus. """
    name = "fedmsg-collectd"
    extra_args = [
        (['--collectd-interval'], {
            'dest': 'collectd_interval',
            'type': int,
            'help': 'Number of seconds to sleep between collectd updates.',
            'default': 2,
        }),
    ]

    def run(self):
        # Initialize the processors before CollectdConsumer is instantiated.
        fedmsg.meta.make_processors(**self.config)

        # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py
        # to work with moksha's expected configuration.
        moksha_options = dict(
            mute=True,  # Disable some warnings.
            zmq_subscribe_endpoints=','.join(
                ','.join(bunch) for bunch in self.config['endpoints'].values()
            ),
        )
        self.config.update(moksha_options)
        self.config[CollectdConsumer.config_key] = True

        CollectdProducer.frequency = datetime.timedelta(
            seconds=self.config['collectd_interval']
        )

        from moksha.hub import main
        main(self.config, [CollectdConsumer], [CollectdProducer],
             framework=False)


def collectd():
    command = CollectdCommand()
    command.execute()
