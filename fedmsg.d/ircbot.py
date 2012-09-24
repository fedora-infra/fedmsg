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
config = dict(
    irc=[
        dict(
            network='irc.freenode.net',
            port=6667,
            nickname='fedmsg-dev',
            channel='fedora-fedmsg',
            timeout=120,
            make_pretty=True,
            make_terse=True,
            # Don't show the heartbeat... gross.
            filters=dict(
                topic=[],
                body=['lub-dub'],
            ),
        ),
    ],
)
