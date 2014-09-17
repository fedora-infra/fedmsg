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
#
import json

from fedmsg.meta.base import BaseProcessor


class LoggerProcessor(BaseProcessor):
    __name__ = "logger"
    __description__ = "miscellaneous Fedora Infrastructure shell scripts"
    __link__ = "https://fedoraproject.org/wiki/Infrastructure"
    __docs__ = "https://fedoraproject.org/wiki/Infrastructure"
    __obj__ = "System Logs"

    def subtitle(self, msg, **config):
        if 'logger.log' in msg['topic']:
            if 'log' in msg['msg']:
                result = msg['msg']['log']
            else:
                result = self._("<custom JSON message>")
            return result + " (%s)" % msg.get('username', 'none')
        else:
            return self._("<unhandled log message>")

    def long_form(self, msg, **config):
        if 'logger.log' in msg['topic'] and 'log' not in msg['msg']:
            result = self._(
                'A custom JSON message was logged by {user}::\n\n{body}')
            user = msg.get('username', '(None)')
            body = '\n'.join(
                json.dumps(dict(msg=msg['msg']), indent=4).split('\n')[1:-1]
            )
            return result.format(user=user, body=body)

    def usernames(self, msg, **config):
        if 'username' in msg:
            return set([msg['username']])
        else:
            # *OLD* messages in datanommer's db don't have a username.
            return set()
