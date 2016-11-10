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
            ssl=False,
            nickname='fedmsg-dev',
            channel='my-fedmsg-channel',
            timeout=120,
            make_pretty=True,
            make_terse=True,
            make_short=True,
            line_rate=0.9,
            # Don't show the heartbeat... gross.
            filters=dict(
                topic=[],
                body=['lub-dub'],
            ),
        ),
    ],
    # the available colors can be looked up from here:
    # https://github.com/fedora-infra/fedmsg/blob/0.16.4/fedmsg/consumers/ircbot.py#L48-L65
    irc_color_lookup={
        "fas": "light blue",
        "bodhi": "green",
        "git": "red",
        "tagger": "brown",
        "wiki": "purple",
        "logger": "orange",
        "pkgdb": "teal",
        "buildsys": "yellow",
        "planet": "light green",
    },

    # color for title if color lookup not defined
    irc_default_color='light grey',

    irc_method='notice',  # Either 'msg' or 'notice'
)
