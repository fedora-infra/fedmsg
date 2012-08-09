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
import time
import datetime

try:
    # py2.7
    from collections import OrderedDict
except ImportError:
    # py2.4, 2.5, 2.6
    from ordereddict import OrderedDict

import json
import json.encoder


class FedMsgEncoder(json.encoder.JSONEncoder):
    """ Encoder with support for __json__ methods. """

    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        if isinstance(obj, datetime.datetime):
            return time.mktime(obj.timetuple())
        return super(FedMsgEncoder, self).default(obj)

# Ensure that the keys are ordered so that messages can be signed
# consistently.  See https://github.com/ralphbean/fedmsg/issues/42
encoder = FedMsgEncoder(sort_keys=True)
dumps = encoder.encode

pretty_encoder = FedMsgEncoder(indent=2)
pretty_dumps = pretty_encoder.encode

loads = json.loads

__all__ = [
    'pretty_dumps',
    'dumps',
    'loads',
]
