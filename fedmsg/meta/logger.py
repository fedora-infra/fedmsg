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
from fedmsg.meta.base import BaseProcessor


class LoggerProcessor(BaseProcessor):
    __name__ = "logger"
    __description__ = "miscellaneous Fedora Infrastructure shell scripts"
    __link__ = "http://fedoraproject.org/wiki/Infrastructure"
    __docs__ = "http://fedoraproject.org/wiki/Infrastructure"
    __obj__ = "System Logs"

    def subtitle(self, msg, **config):
        if 'logger.log' in msg['topic']:
            if 'log' in msg['msg']:
                return msg['msg']['log']
            else:
                return self._("<custom JSON message>")
        else:
            raise NotImplementedError

    def usernames(self, msg, **config):
        if 'username' in msg:
            return set([msg['username']])
        else:
            # *OLD* messages in datanommer's db don't have a username.
            return set()
