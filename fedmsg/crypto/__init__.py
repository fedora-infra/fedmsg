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
""" ``fedmsg.crypto`` - Cryptographic component of fedmsg.

Introduction
------------

In general, we assume that 'everything on the bus is public'.  Even though all
the zmq endpoints are firewalled off from the outside world with iptables, we
do have a forwarding service setup that indiscriminantly
forwards all messages to anyone who wants them.
(See :mod:`fedmsg.commands.gateway.gateway` for that service.)
So, the issue is not encrypting messages so they can't be read.  It is up to
sensitive services like FAS to *not send* sensitive information in the first
place (like passwords, for instance).

However, since at some point, services will respond to and act on messages that
come across the bus, we need facilities for guaranteeing a message comes from
where it *ought* to come from.  (Tangentially, message consumers need a simple
way to declare where they expect their messages to come from and have
the filtering and validation handled for them).

There should also be a convenient way to turn crypto off both globally and
locally.  Justification: a developer may want to work out a bug without any
messages being signed or validated.  In production, certain senders may send
non-critical data from a corner of Fedora Infrastructure in which it's
difficult to sign messages.  A consumer of those messages should be allowed
to ignore validation for those and only those expected unsigned messages

Two backend methods are available to accomplish this:

    - :mod:`fedmsg.crypto.x509`
    - :mod:`fedmsg.crypto.gpg`

Which backend is used is configured by the :term:`crypto_backend` configuration
value.

Certificates
------------

To accomplish message signing, fedmsg must be able to read certificates and a
private key on disk in the case of the :mod:`fedmsg.crypto.x509` backend
or to read public and private GnuPG keys in the came of the
:mod:`fedmsg.crypto.gpg` backend.  For message validation, it only need be
able to read the x509 certificate or gpg public key.  Exactly *which*
certificates are used are determined by looking up the ``certname`` in the
:term:`certnames` config dict.

We use a large number of certs for the deployment of fedmsg.  We have one cert
per `service-host`.  For example, if we have 3 fedmsg-enabled services and each
service runs on 10 hosts, then we have 30 unique certificate/key pairs in all.

The intent is to create difficulty for attackers.  If a low-security service on
a particular box is compromised, we don't want the attacker automatically have
access to the same certificate used for signing high-security service messages.

Furthermore, attempts are made at the sysadmin-level to ensure that
fedmsg-enabled services run as users that have exclusive read access to their
own keys.  See the `Fedora Infrastructure SOP
<http://infrastructure.fedoraproject.org/infra/docs/fedmsg-certs.txt>`_ for
more information (including how to generate new certs/bring up new services).

Routing Policy
--------------

Messages are also checked to see if the name of the certificate they bear and
the topic they're routed on match up in a :term:`routing_policy` dict.  Is the
build server allowed to send messages about wiki updates?  Not if the routing
policy has anything to say about it.

.. note::  By analogy, "signature validation is to authentication as
           routing policy checks are to authorization."

If the topic of a message appears in the :term:`routing_policy`, the name borne
on the certificate must also appear under the associated list of permitted
publishers or the message is marked invalid.

If the topic of a message does *not* appear in the :term:`routing_policy`, two
different courses of action are possible:

    - If :term:`routing_nitpicky` is set to ``False``, then the message is
      given the green light.  Our routing policy doesn't have anything
      specific to say about messages of this topic and so who are we to deny
      it passage, right?
    - If :term:`routing_nitpicky` is set to ``True``, then we deny the message
      and mark it as invalid.

Typically, you'll deploy fedmsg with nitpicky mode turned off.  You can build
your policy over time as you determine what services will be sending what
messages.  Once deployment of fedmsg reaches a certain level of stability, you
can turn nitpicky mode on for enhanced security, but by doing so you may break
certain message paths that you've forgotten to include in your routing policy.

Configuration
-------------

By convention, configuration values for :mod:`fedmsg.crypto` are kept in
``/etc/fedmsg.d/ssl.py``, although technically they can be kept in any
config ``dict`` in ``/etc/fedmsg.d`` (or in any of the config locations checked
by :mod:`fedmsg.config`).

The cryptography routines expect the following values to be defined:

  - :term:`crypto_backend`
  - :term:`crypto_validate_backends`
  - :term:`sign_messages`
  - :term:`validate_signatures`
  - :term:`ssldir`
  - :term:`crl_location`
  - :term:`crl_cache`
  - :term:`crl_cache_expiry`
  - :term:`certnames`
  - :term:`routing_policy`
  - :term:`routing_nitpicky`

For general information on configuration, see :mod:`fedmsg.config`.

Module Contents
---------------

:mod:`fedmsg.crypto` encapsulates standalone functions for:

    - Message signing.
    - Signature validation.
    - Stripping crypto information for view.

See :mod:`fedmsg.crypto.x509` and :mod:`fedmsg.crypto.gpg` for
implementation details.

"""

import copy
import os
import logging

log = logging.getLogger(__name__)

_implementation = None
_validate_implementations = None

from . import gpg
from . import x509

_possible_backends = {
    'gpg': gpg,
    'x509': x509,
}


def init(**config):
    """ Initialize the crypto backend.

    The backend can be one of two plugins:

        - 'x509' - Uses x509 certificates.
        - 'gpg' - Uses GnuPG keys.
    """
    global _implementation
    global _validate_implementations

    if config.get('crypto_backend') == 'gpg':
        _implementation = gpg
    else:
        _implementation = x509

    _validate_implementations = []
    for mod in config.get('crypto_validate_backends', []):
        if mod == 'gpg':
            _validate_implementations.append(gpg)
        elif mod == 'x509':
            _validate_implementations.append(x509)
        else:
            raise ValueError("%r is not a valid crypto backend" % mod)

    if not _validate_implementations:
        _validate_implementations.append(_implementation)


def sign(message, **config):
    """ Insert two new fields into the message dict and return it.

    Those fields are:

        - 'signature' - the computed message digest of the JSON repr.
        - 'certificate' - the base64 certificate or gpg key of the signator.
    """

    if not _implementation:
        init(**config)

    return _implementation.sign(message, **config)


def validate(message, **config):
    """ Return true or false if the message is signed appropriately. """

    if not _validate_implementations:
        init(**config)

    cfg = copy.deepcopy(config)
    if 'gpg_home' not in cfg:
        cfg['gpg_home'] = os.path.expanduser('~/.gnupg/')

    if 'ssldir' not in cfg:
        cfg['ssldir'] = '/etc/pki/fedmsg'

    if 'crypto' in message:
        if not message['crypto'] in _possible_backends:
            log.warn("Message specified an unpossible crypto backend")
            return False
        try:
            backend = _possible_backends[message['crypto']]
        except Exception as e:
            log.warn("Failed to load %r %r" % (message['crypto'], e))
            return False
    # fedmsg 0.7.2 and earlier did not specify which crypto backend a message
    # was signed with.  As long as we care about interoperability with those
    # versions, attempt to guess the backend to use
    elif 'certificate' in message:
        backend = x509
    elif 'signature' in message:
        backend = gpg
    else:
        log.warn('Could not determine crypto backend.  Message unsigned?')
        return False

    if backend in _validate_implementations:
        return backend.validate(message, **cfg)
    else:
        log.warn("Crypto backend %r is disallowed" % backend)
        return False


def validate_signed_by(message, signer, **config):
    """ Validate that a message was signed by a particular certificate.

    This works much like ``validate(...)``, but additionally accepts a
    ``signer`` argument.  It will reject a message for any of the regular
    circumstances, but will also reject it if its not signed by a cert with the
    argued name.
    """

    config = copy.deepcopy(config)
    config['routing_nitpicky'] = True
    config['routing_policy'] = {message['topic']: [signer]}
    return validate(message, **config)


def strip_credentials(message):
    """ Strip credentials from a message dict.

    A new dict is returned without either `signature` or `certificate` keys.
    This method can be called safely; the original dict is not modified.

    This function is applicable using either using the x509 or gpg backends.
    """
    message = copy.deepcopy(message)
    for field in ['signature', 'certificate']:
        if field in message:
            del message[field]
    return message
