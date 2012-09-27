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

Certificates
------------

To accomplish message signing, fedmsg must be able to read certificates and a
private key on disk.  For message validation, it only need be able to read the
certificate.  Exactly *which* certificates are used are determined by looking up
the ``certname`` in the :term:`certnames` config dict.

We use a large number of certs for the deployment of fedmsg.  We have one cert
per `service-host`.  For example, if we have 3 fedmsg-enabled services and each
service runs on 10 hosts, then we have 30 unique certificate/key pairs in all.

The intent is to create difficulty for attackers.  If a low-security service on
a particular box is compromised, we don't want the attacker automatically have
access to the same certificate used for signing high-security service messages.

Furthermore, attempts are made at the sysadmin-level to ensure that
fedmsg-enabled services run as users that have exclusive read access to their
own keys.  See the `Fedora Infrastructure SOP
<http://infrastructure.fedoraproject.org/infra/docs/fedmsg-certs.txt>`_ for more
information (including how to generate new certs/bring up new services).

Configuration
-------------

By convention, configuration values for :mod:`fedmsg.crypto` are kept in
``/etc/fedmsg.d/ssl.py``, although technically they can be kept in any
config ``dict`` in ``/etc/fedmsg.d`` (or in any of the config locations checked
by :mod:`fedmsg.config`).

The cryptography routines expect the following values to be defined:

  - :term:`sign_messages`
  - :term:`validate_signatures`
  - :term:`ssldir`
  - :term:`crl_location`
  - :term:`crl_cache`
  - :term:`crl_cache_expiry`
  - :term:`certnames`

For general information on configuration, see :mod:`fedmsg.config`.

Module Contents
---------------

:mod:`fedmsg.crypto` encapsulates standalone functions for:

    - Message signing.
    - Signature validation.
    - Stripping crypto information for view.

It also contains some hidden/private machinery to handle refreshing a cached
CRL.

"""


import copy
import os
import requests
import time

import fedmsg.encoding

import logging
log = logging.getLogger('fedmsg')

try:
    import M2Crypto
    # FIXME - m2ext will be unnecessary once the following bug is closed.
    # https://bugzilla.osafoundation.org/show_bug.cgi?id=11690
    import m2ext
except ImportError, e:
    log.warn("Crypto disabled %r" % e)


def sign(message, ssldir, certname, **config):
    """ Insert two new fields into the message dict and return it.

    Those fields are:

        - 'signature' - the computed RSA message digest of the JSON repr.
        - 'certificate' - the base64 X509 certificate of the sending host.
    """

    certificate = M2Crypto.X509.load_cert(
        "%s/%s.crt" % (ssldir, certname)).as_pem()
    # FIXME ? -- Opening this file requires elevated privileges in stg/prod.
    rsa_private = M2Crypto.RSA.load_key(
        "%s/%s.key" % (ssldir, certname))

    digest = M2Crypto.EVP.MessageDigest('sha1')
    digest.update(fedmsg.encoding.dumps(message))

    signature = rsa_private.sign(digest.digest())

    # Return a new dict containing the pairs in the original message as well
    # as the new authn fields.
    return dict(message.items() + [
        ('signature', signature.encode('base64')),
        ('certificate', certificate.encode('base64')),
    ])


def validate(message, ssldir, **config):
    """ Return true or false if the message is signed appropriately.

    Three things must be true:

      1) The X509 cert must be signed by our CA
      2) The cert must not be in our CRL.
      3) We must be able to verify the signature using the RSA public key
         contained in the X509 cert.

    Later, a consumer may check that the name on the cert matches the name from
    which they expect a message of this type to originate.
    """

    # TODO -- expose the cert name to the Consumer API so it can do more
    #         fine-grained checks.

    def fail(reason):
        log.warn("Failed validation.  %s" % reason)
        return False

    # Some sanity checking
    for field in ['signature', 'certificate']:
        if not field in message:
            return fail("No %r field found." % field)

    # Peal off the auth datums
    decode = lambda obj: obj.decode('base64')
    signature, certificate = map(decode, (
        message['signature'], message['certificate']))
    message = strip_credentials(message)

    # Build an X509 object
    cert = M2Crypto.X509.load_cert_string(certificate)

    # Validate the cert.  Make sure it is signed by our CA.
    #   validate_certificate will one day be a part of M2Crypto.SSL.Context
    #   https://bugzilla.osafoundation.org/show_bug.cgi?id=11690
    ctx = m2ext.SSL.Context()
    ctx.load_verify_locations(cafile="%s/ca.crt" % ssldir)
    if not ctx.validate_certificate(cert):
        return fail("X509 certificate is not valid.")

    # Load and check against the CRL
    crl = _load_crl(**config)

    # FIXME -- We need to check that the CRL is signed by our own CA.
    # See https://bugzilla.osafoundation.org/show_bug.cgi?id=12954#c2
    #if not ctx.validate_certificate(crl):
    #    return fail("X509 CRL is not valid.")

    # FIXME -- we check the CRL, but by doing string comparison ourselves.
    # This is not what we want to be doing.
    # There is a patch into M2Crypto to handle this for us.  We should use it
    # once its integrated upstream.
    # See https://bugzilla.osafoundation.org/show_bug.cgi?id=12954#c2
    revoked_serials = [long(line.split(': ')[1].strip())
                       for line in crl.as_text().split('\n')
                       if 'Serial Number:' in line]
    if cert.get_serial_number() in revoked_serials:
        return fail("X509 certificate is in the Revocation List (CRL)")

    # If the cert is good, then test to see if the signature in the messages
    # matches up with the provided cert.
    rsa_public = cert.get_pubkey().get_rsa()
    digest = M2Crypto.EVP.MessageDigest('sha1')
    digest.update(fedmsg.encoding.dumps(message))
    try:
        if not rsa_public.verify(digest.digest(), signature):
            raise M2Crypto.RSA.RSAError("RSA signature failed to validate.")
    except M2Crypto.RSA.RSAError as e:
        return fail(str(e))

    return True


def strip_credentials(message):
    """ Strip credentials from a message dict.

    A new dict is returned without either `signature` or `certificate` keys.
    This method can be called safely; the original dict is not modified.
    """
    message = copy.deepcopy(message)
    for field in ['signature', 'certificate']:
        if field in message:
            del message[field]
    return message


def _load_crl(crl_location="https://fedoraproject.org/fedmsg/crl.pem",
              crl_cache="/var/cache/fedmsg/crl.pem",
              crl_cache_expiry=1800,
              **config):
    """ Load the CRL from disk.

    Get a fresh copy from fp.o/fedmsg/crl.pem if ours is getting stale.
    """

    try:
        modtime = os.stat(crl_cache).st_mtime
    except OSError:
        # File does not exist yet.
        modtime = 0

    if time.time() - modtime > crl_cache_expiry:
        try:
            response = requests.get(crl_location)
            with open(crl_cache, 'w') as f:
                f.write(response.content)
        except requests.exceptions.ConnectionError:
            log.warn("Could not access %r" % crl_location)

    return M2Crypto.X509.load_crl(crl_cache)
