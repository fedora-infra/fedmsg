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
import pprint
import re
import threading
import time
import socket

import pygments
import pygments.lexers
import pygments.formatters

import fedmsg
import fedmsg.encoding
import fedmsg.text
from fedmsg.commands import command


extra_args = [
    (['--collectd-interval'], {
        'dest': 'collectd_interval',
        'type': int,
        'help': 'Number of seconds to sleep between collectd updates.',
        'default': 20,
    }),
]


@command(name="fedmsg-collectd", extra_args=extra_args)
def collectd(**kw):
    """ Print out collectd commands indicating activity on the bus. """

    # Build a message formatter
    host = socket.gethostname()
    template = "PUTVAL {host}/fedmsg/{modname} {timestamp}:{value}"

    def formatter(modname, value):
        timestamp = int(time.time())
        return template.format(
            host=host,
            modname=modname,
            timestamp=timestamp,
            value=value,
        )

    fedmsg.text.make_processors(**kw)

    class ConsumerThread(threading.Thread):
        _dict = dict([(p.__name__.lower(), 0) for p in fedmsg.text.processors])

        def run(self):
            kw['publish_endpoint'] = None
            kw['timeout'] = 0
            kw['name'] = 'relay_inbound'
            kw['mute'] = True
            fedmsg.init(**kw)

            for name, ep, topic, message in fedmsg.tail_messages(**kw):
                modname = topic.split('.')[3]
                self._dict[modname] += 1

        def dump(self):
            for k, v in self._dict.items():
                print formatter(k, v)
                # Reset each entry to zero
                self._dict[k] = 0

    t = ConsumerThread()
    t.start()

    while True:
        t.dump()
        time.sleep(kw['collectd_interval'])
