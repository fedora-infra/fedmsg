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
from fedmsg.text.fasshim import gravatar_url


class FASProcessor(BaseProcessor):
    __name__ = "FAS"
    __description__ = "the Fedora Account System"
    __link__ = "https://admin.fedoraproject.org/accounts"
    __docs__ = "https://fedoraproject.org/wiki/Account_System"
    __obj__ = "Account Changes"

    def subtitle(self, msg, **config):
        if 'fas.user.create' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            tmpl = self._(
                "New FAS account:  '{user}'  (created by '{agent}')"
            )
            return tmpl.format(agent=agent, user=user)
        elif 'fas.user.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            fields = ", ".join(msg['msg']['fields'])
            tmpl = self._(
                "{agent} edited the following fields of " +
                "{user}'s FAS profile:  {fields}"
            )
            return tmpl.format(agent=agent, user=user, fields=fields)
        elif 'fas.group.member.' in msg['topic']:
            action = msg['topic'].split('.')[-1]
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            group = msg['msg']['group']['name']
            tmpls = {
                'apply': self._(
                    "{agent} applied for {user}'s membership " +
                    "in the {group} group"
                ),
                'sponsor': self._(
                    "{agent} sponsored {user}'s membership " +
                    "in the {group} group"
                ),
                'remove': self._(
                    "{agent} removed {user} from " +
                    "the {group} group"
                ),
            }
            tmpl = tmpls.get(action, self._(
                '<unhandled action in fedmsg.text.fas>'
            ))
            return tmpl.format(agent=agent, user=user, group=group)
        elif 'fas.group.create' in msg['topic']:
            agent = msg['msg']['agent']['username']
            group = msg['msg']['group']['name']
            tmpl = self._("{agent} created new FAS group {group}")
            return tmpl.format(agent=agent, group=group)
        elif 'fas.group.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            group = msg['msg']['group']['name']
            fields = ", ".join(msg['msg']['fields'])
            tmpl = self._(
                "{agent} edited the following fields of the {group} " +
                "FAS group:  {fields}"
            )
            return tmpl.format(agent=agent, group=group, fields=fields)
        elif 'fas.role.update' in msg['topic']:
            agent = msg['msg']['agent']['username']
            user = msg['msg']['user']['username']
            group = msg['msg']['group']['name']
            tmpl = self._(
                "{agent} changed {user}'s role in the {group} group"
            )
            return tmpl.format(agent=agent, group=group, user=user)
        else:
            raise NotImplementedError

    def icon(self, msg, **config):
        return "https://admin.fedoraproject.org/accounts/static/" + \
               "theme/fas/images/account.png"

    def secondary_icon(self, msg, **config):
        # Every fas fedmsg message has an "agent" field.. "whodunnit"
        return gravatar_url(username=msg['msg']['agent']['username'])
