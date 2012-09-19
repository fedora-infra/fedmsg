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
""" :mod:`fedmsg.encoding.sqla` houses utility functions for JSONifying
sqlalchemy models that do not define their own ``.__json__()`` methods.

Use at your own risk.  :func:`fedmsg.encoding.sqla.to_json` will expose all
attributes and relations of your sqlalchemy object and may expose information
you not want it to.  See :doc:`crypto` for considerations.
"""

try:
    from sqlalchemy.orm import class_mapper
    from sqlalchemy.orm.properties import RelationshipProperty
except ImportError:
    pass


def to_json(obj, seen=None):
    """ Returns a dict representation of the object.

    Recursively evaluates to_json(...) on its relationships.
    """

    if not seen:
        seen = []

    properties = list(class_mapper(type(obj)).iterate_properties)
    relationships = [
        p.key for p in properties if type(p) is RelationshipProperty
    ]
    attrs = [
        p.key for p in properties if p.key not in relationships
    ]

    d = dict([(attr, getattr(obj, attr)) for attr in attrs])

    for attr in relationships:
        d[attr] = expand(obj, getattr(obj, attr), seen)

    return d


def expand(obj, relation, seen):
    """ Return the to_json or id of a sqlalchemy relationship. """

    if hasattr(relation, 'all'):
        relation = relation.all()

    if hasattr(relation, '__iter__'):
        return [expand(obj, item, seen) for item in relation]

    if type(relation) not in seen:
        return to_json(relation, seen + [type(obj)])
    else:
        return relation.id
