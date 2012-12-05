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

import fedmsg
from fedmsg.commands import BaseCommand


class AnnounceCommand(BaseCommand):
    """
    Emit an announcement message to the FI bus.

    Example::

        $ echo "Fedora Core 4 has been declared GOLD" | fedmsg-announce \
                --link http://fedoraproject.org/news

    Technically this command is a simpler version of fedmsg-logger that emits
    on a special topic.  It is expected that :term:`routing_policy` is
    specified such that only restricted parties can issue fedmsg announcements.

    This command expects its message to come from stdin.
    """

    name = "fedmsg-announce"
    extra_args = [
        (['--link'], {
            'dest': 'link',
            'metavar': "URL",
            'default': None,
            'help': "Specify a link to go along with the announcement.",
        }),
    ]

    def run(self):
        # This specifies that a special certificate should be used to sign this
        # message.  At the sysadmin level, you are responsible for taking care
        # of two things:
        #   1) That the announce cert is readable only by appropriate persons.
        #   2) That the routing_policy is setup so that "announce.announcement"
        #      messages are valid only if signed by such a certificate.
        self.config['cert_prefix'] = "announce"

        # This just specifies that we should be talking to the fedmsg-relay.
        self.config['active'] = True
        self.config['name'] = 'relay_inbound'
        fedmsg.init(**self.config)

        # Read in and setup our message.  Include --link, even if it is None.
        message = "\n".join(map(str.strip, sys.stdin.readlines()))
        msg = dict(message=message, link=self.config['link'])

        # Fire!
        fedmsg.publish(modname="announce", topic="announcement", msg=msg)


def announce():
    command = AnnounceCommand()
    command.execute()
