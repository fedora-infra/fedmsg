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
try:
    # Else we need M2Crypto and m2ext
    import M2Crypto
    import m2ext
    _m2crypto = True
except ImportError:
    _m2crypto = False

from .utils import _load_remote_cert, validate_policy
from .x509_ng import _cryptography, sign as _crypto_sign, validate as _crypto_validate
import fedmsg.crypto  # noqa: E402
import fedmsg.encoding  # noqa: E402


log = logging.getLogger(__name__)

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


def _m2crypto_sign(message, ssldir=None, certname=None, **config):
    """ Insert two new fields into the message dict and return it.

    Those fields are:

        - 'signature' - the computed RSA message digest of the JSON repr.
        - 'certificate' - the base64 X509 certificate of the sending host.
    """
    if ssldir is None or certname is None:
        error = "You must set the ssldir and certname keyword arguments."
        raise ValueError(error)

    message['crypto'] = 'x509'

    certificate = M2Crypto.X509.load_cert(
        "%s/%s.crt" % (ssldir, certname)).as_pem()
    # Opening this file requires elevated privileges in stg/prod.
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


def _m2crypto_validate(message, ssldir=None, **config):
    """ Return true or false if the message is signed appropriately.

    Four things must be true:

      1) The X509 cert must be signed by our CA
      2) The cert must not be in our CRL.
      3) We must be able to verify the signature using the RSA public key
         contained in the X509 cert.
      4) The topic of the message and the CN on the cert must appear in the
         :term:`routing_policy` dict.

    """

    if ssldir is None:
        raise ValueError("You must set the ssldir keyword argument.")

    def fail(reason):
        log.warn("Failed validation.  %s" % reason)
        return False

    # Some sanity checking
    for field in ['signature', 'certificate']:
        if field not in message:
            return fail("No %r field found." % field)
        if not isinstance(message[field], str):
            return fail("msg[%r] is not a string" % field)

    # Peal off the auth datums
    signature = message['signature'].decode('base64')
    certificate = message['certificate'].decode('base64')
    message = fedmsg.crypto.strip_credentials(message)

    # Build an X509 object
    cert = M2Crypto.X509.load_cert_string(certificate)

    # Validate the cert.  Make sure it is signed by our CA.
    #   validate_certificate will one day be a part of M2Crypto.SSL.Context
    #   https://bugzilla.osafoundation.org/show_bug.cgi?id=11690

    default_ca_cert_loc = 'https://fedoraproject.org/fedmsg/ca.crt'
    cafile = _load_remote_cert(
        config.get('ca_cert_location', default_ca_cert_loc),
        config.get('ca_cert_cache', '/etc/pki/fedmsg/ca.crt'),
        config.get('ca_cert_cache_expiry', 0),
        **config)

    ctx = m2ext.SSL.Context()
    ctx.load_verify_locations(cafile=cafile)
    if not ctx.validate_certificate(cert):
        return fail("X509 certificate is not valid.")

    # Load and check against the CRL
    crl = None
    if 'crl_location' in config and 'crl_cache' in config:
        crl = _load_remote_cert(
            config.get('crl_location', 'https://fedoraproject.org/fedmsg/crl.pem'),
            config.get('crl_cache', '/var/cache/fedmsg/crl.pem'),
            config.get('crl_cache_expiry', 1800),
            **config)
    if crl:
        crl = M2Crypto.X509.load_crl(crl)
        # FIXME -- We need to check that the CRL is signed by our own CA.
        # See https://bugzilla.osafoundation.org/show_bug.cgi?id=12954#c2
        # if not ctx.validate_certificate(crl):
        #    return fail("X509 CRL is not valid.")

        # FIXME -- we check the CRL, but by doing string comparison ourselves.
        # This is not what we want to be doing.
        # There is a patch into M2Crypto to handle this for us.  We should use it
        # once its integrated upstream.
        # See https://bugzilla.osafoundation.org/show_bug.cgi?id=12954#c2
        revoked_serials = [long(line.split(': ')[1].strip(), base=16)
                           for line in crl.as_text().split('\n')
                           if 'Serial Number:' in line]
        if cert.get_serial_number() in revoked_serials:
            subject = cert.get_subject()

            signer = '(no CN)'
            if subject.nid.get('CN'):
                entry = subject.get_entries_by_nid(subject.nid['CN'])[0]
                if entry:
                    signer = entry.get_data().as_text()

            return fail("X509 cert %r, %r is in the Revocation List (CRL)" % (
                signer, cert.get_serial_number()))

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

    # Now we know that the cert is valid.  The message is *authenticated*.
    # * Next step:  Authorization *

    # Load our policy from the config dict.
    routing_policy = config.get('routing_policy', {})

    # Determine the name of the signer of the message.
    # This will be something like "shell-pkgs01.stg.phx2.fedoraproject.org"
    subject = cert.get_subject()
    signer = subject.get_entries_by_nid(subject.nid['CN'])[0]\
        .get_data().as_text()

    return validate_policy(
        message.get('topic'), signer, routing_policy, config.get('routing_nitpicky', False))


# Maintain the ``sign`` and ``validate`` APIs while preferring cryptography and
# pyOpenSSL over M2Crypto.
if _cryptography:
    sign = _crypto_sign
    validate = _crypto_validate
elif _m2crypto:
    sign = _m2crypto_sign
    validate = _m2crypto_validate
else:
    sign = _disabled_sign
    validate = _disabled_validate
