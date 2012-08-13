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
    def handle_subtitle(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'fedoratagger.tag.update',
                'fedoratagger.tag.create',
                'fedoratagger.login.tagger',
            ]
        ])

    def subtitle(self, msg, **config):
        if 'fedoratagger.tag.update' in msg['topic']:
            user = msg['msg']['user']['username']
            tag = msg['msg']['tag']['tag']
            tmpl = self._("{user} voted on the package tag '{tag}'")
            return tmpl.format(user=user, tag=tag)
        elif 'fedoratagger.tag.create' in msg['topic']:
            tag = msg['msg']['tag']['tag']
            tmpl = self._('Added new tag "{tag}"')
            return tmpl.format(tag=tag)
        elif 'fedoratagger.login.tagger' in msg['topic']:
            user = msg['msg']['user']['username']
            tmpl = self._("{user} logged in to fedoratagger")
            return tmpl.format(user=user)
        else:
            raise NotImplementedError
