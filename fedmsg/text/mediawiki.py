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


class WikiProcessor(BaseProcessor):
    __name__ = "Wiki"
    __description__ = "the Fedora Wiki"
    __link__ = "https://fedoraproject.org/wiki"
    __docs__ = "https://fedoraproject.org/wiki"
    __obj__ = "Wiki Edits"

    def handle_subtitle(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'wiki.article.edit',
                'wiki.upload.complete',
            ]
        ])

    def subtitle(self, msg, **config):
        if 'wiki.article.edit' in msg['topic']:
            user = msg['msg']['user']
            title = msg['msg']['title']
            tmpl = self._('{user} made a wiki edit to "{title}".')
            return tmpl.format(user=user, title=title)
        elif 'wiki.upload.complete' in msg['topic']:
            user = msg['msg']['user_text']
            filename = msg['msg']['title']['mPrefixedText']
            description = msg['msg']['description'][:35]
            tmpl = self._(
                '{user} uploaded {filename} to the wiki: "{description}..."'
            )
            return tmpl.format(user=user, filename=filename,
                               description=description)
        else:
            raise NotImplementedError

    def handle_link(self, msg, **config):
        return any([
            target in msg['topic'] for target in [
                'wiki.article.edit',
            ]
        ])

    def link(self, msg, **config):
        if 'wiki.article.edit' in msg['topic']:
            return msg['msg']['url']
        else:
            raise NotImplementedError

    def handle_icon(self, msg, **config):
        return any([target in msg['topic'] for target in [
            'wiki.article.edit',
            'wiki.upload.complete',
        ]])

    def icon(self, msg, **config):
        return "https://upload.wikimedia.org/wikipedia/commons/thumb" + \
               "/3/3d/Mediawiki-logo.png/53px-Mediawiki-logo.png"
