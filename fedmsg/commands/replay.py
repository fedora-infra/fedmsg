# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
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
from __future__ import print_function

import requests
import sys

import fedmsg
from fedmsg.commands import BaseCommand


class ReplayCommand(BaseCommand):
    """ Replay a message from the datagrepper history on your local bus. """

    name = "fedmsg-dg-replay"
    extra_args = [
        (['--msg-id'], {
            'dest': 'msg_id',
            'help': 'The msg_id of the message you want to replay.',
            'default': None,
        }),
        (['--datagrepper-url'], {
            'dest': 'datagrepper_url',
            'help': 'The URL of a datagrepper instance to query for history.',
            'default': 'https://apps.fedoraproject.org/datagrepper',
        }),
    ]

    def run(self):
        self.config['active'] = True
        self.config['name'] = 'relay_inbound'
        fedmsg.init(**self.config)

        idx = self.config.get('msg_id')
        if not idx:
            print("--msg-id is required")
            sys.exit(1)

        print("Retrieving %r" % idx)
        url = self.config['datagrepper_url'] + "/id"
        resp = requests.get(url, params={'id': idx})

        code = resp.status_code
        if code != 200:
            print("datagrepper request of %r failed. Status: %r" % (idx, code))
            sys.exit(2)

        msg = resp.json()
        tokens = msg['topic'].split('.')
        modname = tokens[4]
        topic = '.'.join(tokens[5:])

        print("Broadcasting %r" % idx)
        fedmsg.publish(modname=modname, topic=topic, msg=msg['msg'])
        print("OK.")


def replay():
    command = ReplayCommand()
    return command.execute()
