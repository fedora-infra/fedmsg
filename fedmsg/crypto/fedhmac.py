# This file is part of fedmsg.
# Copyright (C) 2017 Pierre-Yves Chibon <pingou@pingoured.fr>
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
# Authors:  Pierre-Yves Chibon <pingou@pingoured.fr>
#           Ralph Bean <rbean@redhat.com>

import os
import hashlib
import hmac

import six


import logging
log = logging.getLogger(__name__)


class GpgBinaryError(Exception):
    pass


# Here comes the part actually relevent to fedmsg
""" ``fedmsg.crypto.hmac`` - Simple hmac backend for :mod:`fedmsg.crypto` """
import fedmsg.encoding


def sign(message, hmac_token, hash_method=None, **config):
    """ Insert a new field into the message dict and return it.

    The new field is:

        - 'hmac - the computed hmac digest of the JSON repr
          of the `msg` field.
    """

    message['crypto'] = 'hmac'

    if hash_method is None:
        hash_method = 'sha526'

    if not hasattr(hashlib, hash_method):
        raise HmacError('Invalid hash method: %s' % hash_method)

    signature = hmac.new(
        hmac_token,
        fedmsg.encoding.dumps(message['msg']),
        getattr(hashlib, hash_method),
    )
    return dict(list(message.items()) + [('hmac', signature.hexdigest())])


def validate(message, hmac_token, hash_method=None, **config):
    """ Return true or false if the message is signed appropriately.

    Two things must be true:

        1) The signature must be valid (obviously)
        2) The hmac token on the receiving end must be 
           the same as on the sending end.
    """
    if hash_method is None:
        hash_method = 'sha526'

    if not hasattr(hashlib, hash_method):
        raise HmacError('Invalid hash method: %s' % hash_method)

    signature = hmac.new(
        hmac_token,
        fedmsg.encoding.dumps(message['msg']),
        getattr(hashlib, hash_method),
    ).hexdigest()

    if signature == message['hmac']:
        return True
    else:
        log.warn("Failed validation. {0} != {1}".format(signature, message['hmac']))
        return False
