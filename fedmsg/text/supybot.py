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
from fedmsg.text.base import BaseProcessor


class SupybotProcessor(BaseProcessor):
    def handle_subtitle(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'meetbot.meeting.start',
                'meetbot.meeting.complete',
            ]
        ])

    def handle_link(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'meetbot.meeting.complete',
            ]
        ])

    def link(self, msg, **config):
        return msg['msg']['url'] + ".html"

    def subtitle(self, msg, **config):
        if 'meetbot.meeting.start' in msg['topic']:
            if msg['msg']['meeting_topic']:
                tmpl = self._('{user} started meeting "{name}" in {channel}')
            else:
                tmpl = self._('{user} started a meeting in {channel}')
        elif 'meetbot.meeting.complete' in msg['topic']:
            if msg['msg']['meeting_topic']:
                tmpl = self._('{user} ended meeting "{name}" in {channel}')
            else:
                tmpl = self._('{user} ended a meeting in {channel}')
        else:
            raise NotImplementedError

        user = msg['msg']['owner']
        name = msg['msg']['meeting_topic']
        channel = msg['msg']['channel']

        return tmpl.format(user=user, name=name, channel=channel)
