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


class TaggerProcessor(BaseProcessor):
    __name__ = "Tagger"
    __description__ = "the Fedora package labeller/tagger"
    __link__ = "https://apps.fedoraproject.org/tagger"
    __docs__ = "https://github.com/ralphbean/fedora-tagger"
    __obj__ = "Package Tag Votes"

    def handle_subtitle(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'fedoratagger.tag.update',
                'fedoratagger.tag.create',
            ]
        ])

    def handle_link(self, msg, **config):
        if not isinstance(msg.get('msg', {}), dict):
            return False

        vote = msg.get('msg', {}).get('vote', {})
        pack = vote.get('tag', {}).get('package', {})
        return pack and '.fedoratagger.' in msg['topic']

    def link(self, msg, **config):
        vote = msg.get('msg', {}).get('vote', {})
        pack = vote.get('tag', {}).get('package', {})
        return "https://apps.fedoraproject.org/tagger/" + pack.keys()[0]

    def subtitle(self, msg, **config):
        if 'fedoratagger.tag.update' in msg['topic']:
            user = msg['msg']['vote']['user']['username']
            tag = msg['msg']['vote']['tag']['tag']
            package = msg['msg']['vote']['tag']['package'].keys()[0]

            if msg['msg']['vote']['like']:
                verb = "up"
            else:
                verb = "down"

            tmpl = self._('{user} {verb}voted "{tag}" on {package}')
            return tmpl.format(user=user, tag=tag, verb=verb, package=package)
        elif 'fedoratagger.tag.create' in msg['topic']:
            user = msg['msg']['vote']['user']['username']
            tag = msg['msg']['vote']['tag']['tag']
            package = msg['msg']['vote']['tag']['package'].keys()[0]
            tmpl = self._('{user} added tag "{tag}" to {package}')
            return tmpl.format(user=user, tag=tag, package=package)
        else:
            raise NotImplementedError
