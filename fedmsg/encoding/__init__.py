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
""" fedmsg messages are encoded as JSON.

Use the functions :func:`fedmsg.encoding.loads`, :func:`fedmsg.encoding.dumps`,
and :func:`fedmsg.encoding.pretty_dumps` to encode/decode.

When serializing objects (usually python dicts) with
:func:`fedmsg.encoding.dumps` and :func:`fedmsg.encoding.pretty_dumps`, the
following exceptions to normal JSON serialization are observed.

 * :class:`datetime.datetime` objects are correctly converted to seconds since
   the epoch.
 * For objects that are not JSON serializable, if they have a ``.__json__()``
   method, that will be used instead.
 * SQLAlchemy models that do not specify a ``.__json__()`` method will be run
   through :func:`fedmsg.encoding.sqla.to_json` which recursively produces a
   dict of all attributes and relations of the object(!)  Be careful using
   this, as you might expose information to the bus that you do not want to.
   See :doc:`crypto` for considerations.

"""

import time
import datetime

sqlalchemy = None
try:
    import sqlalchemy
    import sqlalchemy.ext.declarative
except ImportError:
    pass

try:
    # py2.7
    from collections import OrderedDict
except ImportError:
    # py2.4, 2.5, 2.6
    from ordereddict import OrderedDict

import json
import json.encoder


class FedMsgEncoder(json.encoder.JSONEncoder):
    """ Encoder with convenience support. """

    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        if isinstance(obj, datetime.datetime):
            return time.mktime(obj.timetuple())
        if isinstance(obj, time.struct_time):
            return time.mktime(obj)
        if isinstance(obj, set):
            return list(obj)
        if sqlalchemy:
            # As a last ditch, try using our sqlalchemy json encoder.
            sqla_type = sqlalchemy.ext.declarative.DeclarativeMeta
            if isinstance(type(obj), sqla_type):
                import fedmsg.encoding.sqla
                return fedmsg.encoding.sqla.to_json(obj)

        return super(FedMsgEncoder, self).default(obj)


# Ensure that the keys are ordered so that messages can be signed
# consistently.  See https://github.com/fedora-infra/fedmsg/issues/42
encoder = FedMsgEncoder(sort_keys=True, separators=(',', ':'))
dumps = encoder.encode

pretty_encoder = FedMsgEncoder(indent=2)
pretty_dumps = pretty_encoder.encode

loads = json.loads

__all__ = [
    'pretty_dumps',
    'dumps',
    'loads',
]
