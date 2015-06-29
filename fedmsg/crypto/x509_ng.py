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


import base64
import os
import requests
import time

import fedmsg.crypto
import fedmsg.encoding

import logging
log = logging.getLogger(__name__)

import cryptography.x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import asymmetric, hashes, serialization

import six

if six.PY3:
    long = int


def sign(message, ssldir=None, certname=None, **config):
    """ Insert two new fields into the message dict and return it.

    Those fields are:

        - 'signature' - the computed RSA message digest of the JSON repr.
        - 'certificate' - the base64 X509 certificate of the sending host.
    """

    if ssldir is None or certname is None:
        error = "You must set the ssldir and certname keyword arguments."
        raise ValueError(error)

    message['crypto'] = 'x509'

    with open("%s/%s.crt" % (ssldir, certname), "rb") as f:
        data = f.read()
        certificate = cryptography.x509.load_pem_x509_certificate(
            data,
            default_backend()
        )
        # TODO: it seems that there's no way in cryptography to
        #  get back the PEM block of loaded certificate
        cert_pem = data[data.decode('utf-8').find('-----BEGIN'):]

    # Opening this file requires elevated privileges in stg/prod.
    with open("%s/%s.key" % (ssldir, certname), "rb") as f:
        rsa_private = serialization.load_pem_private_key(
            data=f.read(),
            password=None,
            backend=default_backend()
        )

    signer = rsa_private.signer(
        asymmetric.padding.PKCS1v15(),
        hashes.SHA1()
    )
    signer.update(fedmsg.encoding.dumps(message).encode('utf-8'))
    signature = signer.finalize()

    # Return a new dict containing the pairs in the original message as well
    # as the new authn fields.
    return dict(list(message.items()) + [
        ('signature', base64.b64encode(signature).decode('utf-8')),
        ('certificate', base64.b64encode(cert_pem).decode('utf-8')),
    ])


def validate(message, ssldir=None, **config):
    """ Return true or false if the message is signed appropriately.

    Four things must be true:

      1) The X509 cert must be signed by our CA
      2) The cert must not be in our CRL.
      3) We must be able to verify the signature using the RSA public key
         contained in the X509 cert.
      4) The topic of the message and the CN on the cert must appear in the
         :term:`routing_policy` dict.

    """

    import M2Crypto
    import m2ext

    if ssldir is None:
        raise ValueError("You must set the ssldir keyword argument.")

    def fail(reason):
        log.warn("Failed validation.  %s" % reason)
        return False

    # Some sanity checking
    for field in ['signature', 'certificate']:
        if not field in message:
            return fail("No %r field found." % field)
        # TODO: should this be six.binary_type?
        if not isinstance(message[field], six.binary_type):
            return fail("msg[%r] is not a string" % field)

    # Peal off the auth datums
    decode = lambda obj: obj.decode('base64')
    signature, certificate = map(decode, (
        message['signature'], message['certificate']))
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
    crl = _load_remote_cert(
        config.get('crl_location', 'https://fedoraproject.org/fedmsg/crl.pem'),
        config.get('crl_cache', '/var/cache/fedmsg/crl.pem'),
        config.get('crl_cache_expiry', 1800),
        **config)
    crl = M2Crypto.X509.load_crl(crl)

    # FIXME -- We need to check that the CRL is signed by our own CA.
    # See https://bugzilla.osafoundation.org/show_bug.cgi?id=12954#c2
    #if not ctx.validate_certificate(crl):
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

    # Perform the authz dance
    # Do we have a list of permitted senders for the topic of this message?
    if message.get('topic') in routing_policy:
        # If so.. is the signer one of those permitted senders?
        if signer in routing_policy[message['topic']]:
            # We are good.  The signer of this message is explicitly
            # whitelisted to send on this topic in our config policy.
            pass
        else:
            # We have a policy for this topic and $homeboy isn't on the list.
            return fail("Authorization/routing_policy error.  "
                        "Topic %r.  Signer %r." % (message['topic'], signer))
    else:
        # We don't have a policy for this topic.  How we react next for an
        # underspecified routing_policy is based on a configuration option.

        # Ideally, we are in nitpicky mode.  We leave it disabled while
        # standing up fedmsg across our environment so that we can build our
        # policy without having the whole thing come crashing down.
        if config.get('routing_nitpicky', False):
            # We *are* in nitpicky mode.  We don't have an entry in the
            # routing_policy for the topic of this message.. and *nobody*
            # gets in without a pass.  That means that we fail the message.
            return fail("Authorization/routing_policy underspecified.")
        else:
            # We are *not* in nitpicky mode.  We don't have an entry in the
            # routing_policy for the topic of this message.. but we don't
            # really care.  We pass on the message and ultimately return
            # True later on.
            pass

    return True


def _load_remote_cert(location, cache, cache_expiry, **config):
    """ Get a fresh copy from fp.o/fedmsg/crl.pem if ours is getting stale.

    Return the local filename.
    """

    try:
        modtime = os.stat(cache).st_mtime
    except OSError:
        # File does not exist yet.
        modtime = 0

    if (
        (not modtime and not cache_expiry) or
        (cache_expiry and time.time() - modtime > cache_expiry)
    ):
        try:
            response = requests.get(location)
            with open(cache, 'w') as f:
                f.write(response.content)
        except requests.exceptions.ConnectionError:
            log.error("Could not access %r" % location)
            raise
        except IOError:
            # If we couldn't write to the specified cache location, try a
            # similar place but inside our home directory instead.
            cache = os.path.expanduser("~/.local" + cache)
            usr_dir = '/'.join(cache.split('/')[:-1])

            if not os.path.isdir(usr_dir):
                os.makedirs(usr_dir)

            with open(cache, 'w') as f:
                f.write(response.content)

    return cache
