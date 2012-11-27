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
import logging
import socket
import time
import sys

import pygments
import pygments.lexers
import pygments.formatters

import fedmsg
import fedmsg.encoding
import fedmsg.meta

from fedmsg.commands import command
from fedmsg.consumers import FedmsgConsumer
from moksha.hub.api import PollingProducer
from kitchen.iterutils import iterate

extra_args = [
    (['--collectd-interval'], {
        'dest': 'collectd_interval',
        'type': int,
        'help': 'Number of seconds to sleep between collectd updates.',
        'default': 5,
    }),
]


class CollectdConsumer(FedmsgConsumer):
    topic = "org.fedoraproject.*"
    config_key = "fedmsg.commands.collectd.enabled"
    validate_messages = False

    def __init__(self, hub):
        super(CollectdConsumer, self).__init__(hub)
        self._dict = dict([
            (p.__name__.lower(), 0) for p in fedmsg.meta.processors
        ])
        self.host = socket.gethostname()

    def consume(self, msg):
        modname = msg['topic'].split('.')[3]
        self._dict[modname] += 1

    def dump(self):
        """ Called by CollectdProducer every `n` seconds. """

        # Print out the collectd feedback.
        print self.formatter([v for k, v in sorted(self._dict.items())])

        # Reset each entry to zero
        for k, v in sorted(self._dict.items()):
            self._dict[k] = 0

    def formatter(self, values):
        """ Format messages for collectd to consume. """
        template = "PUTVAL {host}/fedmsg/fedmsg_scoreboard interval={interval} {timestamp}:{values}"
        timestamp = int(time.time())
        return template.format(
            host=self.host,
            timestamp=timestamp,
            values=":".join(map(str, values)),
            interval=self.hub.config['collectd_interval'],
        )


class CollectdProducer(PollingProducer):
    # "Frequency" is set later at runtime.
    def poll(self):
        self.hub.consumers[0].dump()


@command(name="fedmsg-collectd", extra_args=extra_args)
def collectd(**kw):
    """ Print machine-readable information for collectd to monitor the bus. """

    # Initialize the processors before CollectdConsumer is instantiated.
    fedmsg.meta.make_processors(**kw)

    # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to work
    # with moksha's expected configuration.
    moksha_options = dict(
        mute=True,  # Disable some warnings.
        zmq_subscribe_endpoints=','.join(
            ','.join(bunch) for bunch in kw['endpoints'].values()
        ),
    )
    kw.update(moksha_options)
    kw[CollectdConsumer.config_key] = True

    CollectdProducer.frequency = datetime.timedelta(
        seconds=kw['collectd_interval']
    )

    # Turn off moksha logging.
    logging.disable(logging.INFO)
    logging.disable(logging.WARN)

    from moksha.hub import main
    main(kw, [CollectdConsumer], [CollectdProducer])
