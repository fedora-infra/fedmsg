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
import sys
from fabulous.color import red, green

import fedmsg
from fedmsg.commands import command


def _colorize(success):
    if success:
        return green("  OK  ")
    else:
        return red(" FAIL ")

extra_args = []


@command(name="fedmsg-status", extra_args=extra_args)
def status(**kwargs):
    """ Check the status of fedmsg-hub instances.

    This command is a work in progress.  For the moment, it returns results for
    every endpoint listed in `fedmsg-config`, but not every endpoint is
    associated with a hub.  Many are associated with WSGI processes which have
    no fedmsg heartbeat.  Lots of false alarms will be reported until this is
    resolved.
    """

    # Disable sending
    fedmsg.init(**kwargs)

    status = fedmsg.have_pulses(**kwargs)

    padding = max(map(len, kwargs['endpoints']))
    for name, endpoint, success in fedmsg.have_pulses(**kwargs):
        print "[%s]  %s %s" % (
            _colorize(success),
            name.rjust(padding),
            endpoint,
        )
