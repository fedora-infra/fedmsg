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
""" ``fedmsg.crypto.x509`` - X.509 backend for :mod:`fedmsg.crypto`.  """

import logging
import warnings

import six
from .x509_ng import _cryptography, sign as _crypto_sign, validate as _crypto_validate


_log = logging.getLogger(__name__)

if six.PY3:
    long = int


def _disabled_sign(*args, **kwargs):
    """A fallback function that emits a warning when no crypto is being used."""
    warnings.warn('Message signing is disabled because "cryptography" and '
                  '"pyopenssl" or "m2crypto" are not available.')


def _disabled_validate(*args, **kwargs):
    """A fallback function that emits a warning when no crypto is being used."""
    warnings.warn('Message signature validation is disabled because ("cryptography"'
                  ' and "pyopenssl") or "m2crypto" are not available.')


# Maintain the ``sign`` and ``validate`` APIs
if _cryptography:
    sign = _crypto_sign
    validate = _crypto_validate
else:
    sign = _disabled_sign
    validate = _disabled_validate
