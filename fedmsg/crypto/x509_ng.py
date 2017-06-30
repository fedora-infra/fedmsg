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
import base64

try:
    # We require cryptography 1.6+ and pyOpenSSL 16.1+
    #
    # Until cryptography can do full chain certificate validation
    # (https://github.com/pyca/cryptography/issues/2381) we need to use
    # pyOpenSSL. However, pyOpenSSL is not meant to be a long-term solution
    # since the ultimate goal is for it to be obsoleted:
    # https://mail.python.org/pipermail/cryptography-dev/2017-June/000774.html
    from cryptography import x509
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import asymmetric, hashes, serialization
    from OpenSSL.crypto import (X509Store, X509StoreContext, X509StoreContextError,
                                load_certificate, load_crl, FILETYPE_PEM, X509StoreFlags)
    _cryptography = True
except ImportError:  # pragma: no cover
    _cryptography = False

from . import utils
import fedmsg.crypto
import fedmsg.encoding


_log = logging.getLogger(__name__)


def sign(message, ssldir=None, certname=None, **config):
    """Insert two new fields into the message dict and return it.

    Those fields are:

        - 'signature' - the computed RSA message digest of the JSON repr.
        - 'certificate' - the base64 X509 certificate of the sending host.

    Arg:
        message (dict): An unsigned message to sign.
        ssldir (str): The absolute path to the directory containing the SSL certificates to
            use.
        certname (str): The name of the key pair to sign the message with. This corresponds to
            the filenames within ``ssldir`` sans prefixes. The key pair must be named
            ``<certname>.key`` and ``<certname>.crt``
    Returns:
        dict: The signed message.
    """
    if ssldir is None or certname is None:
        error = "You must set the ssldir and certname keyword arguments."
        raise ValueError(error)

    message['crypto'] = 'x509'

    with open("%s/%s.key" % (ssldir, certname), "rb") as f:
        rsa_private = serialization.load_pem_private_key(
            data=f.read(),
            password=None,
            backend=default_backend()
        )

    signature = rsa_private.sign(
        fedmsg.encoding.dumps(message).encode('utf-8'),
        asymmetric.padding.PKCS1v15(),
        hashes.SHA1(),
    )

    with open("%s/%s.crt" % (ssldir, certname), "rb") as f:
        cert = x509.load_pem_x509_certificate(f.read(), default_backend())
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)

    return _prep_crypto_msg(dict(list(message.items()) + [
        ('signature', base64.b64encode(signature)),
        ('certificate', base64.b64encode(cert_pem)),
    ]))


def _prep_crypto_msg(message):
    """Split the signature and certificate in the same way M2Crypto does.

    M2Crypto is dropping newlines into its signature and certificate. This
    exists purely to maintain backwards compatibility.

    Args:
        message (dict): A message with the ``signature`` and ``certificate`` keywords.

    Returns:
        dict: The same message, but with the values of ``signature`` and ``certificate``
            split every 76 characters with a newline and a final newline at the end.
    """
    signature = message['signature']
    certificate = message['certificate']
    sliced_signature, sliced_certificate = [], []
    for x in range(0, len(signature), 76):
        sliced_signature.append(signature[x:x+76])
    for x in range(0, len(certificate), 76):
        sliced_certificate.append(certificate[x:x+76])

    message['signature'] = '\n'.join(sliced_signature) + '\n'
    message['certificate'] = '\n'.join(sliced_certificate) + '\n'
    return message


def validate(message, ssldir=None, **config):
    """
    Validate the signature on the given message.

    Four things must be true for the signature to be valid:

      1) The X.509 cert must be signed by our CA
      2) The cert must not be in our CRL.
      3) We must be able to verify the signature using the RSA public key
         contained in the X.509 cert.
      4) The topic of the message and the CN on the cert must appear in the
         :term:`routing_policy` dict.

    Args:
        message (dict): A signed message in need of validation. A signed message
            contains the 'signature' and 'certificate' keys.
        ssldir (str): The path to the directory containing PEM-encoded X.509
            key pairs.

    Returns:
        bool: True of the message passes validation, False otherwise.
    """
    try:
        signature = message['signature'].decode('base64')
        certificate = message['certificate'].decode('base64')
    except KeyError:
        return False

    message = fedmsg.crypto.strip_credentials(message)

    crl_file = None
    if 'crl_location' in config and 'crl_cache' in config:
        crl_file = utils._load_remote_cert(
            config.get('crl_location', 'https://fedoraproject.org/fedmsg/crl.pem'),
            config.get('crl_cache', '/var/cache/fedmsg/crl.pem'),
            config.get('crl_cache_expiry', 1800),
            **config
        )

    ca_file = utils._load_remote_cert(
        config.get('ca_cert_location', 'https://fedoraproject.org/fedmsg/ca.crt'),
        config.get('ca_cert_cache', '/etc/pki/fedmsg/ca.crt'),
        config.get('ca_cert_cache_expiry', 0),
        **config
    )

    with open(ca_file, 'rb') as fd:
        ca_certificate = fd.read()

    crl = None
    if crl_file:
        with open(crl_file, 'rb') as fd:
            crl = fd.read()

    try:
        _validate_signing_cert(ca_certificate, certificate, crl)
    except X509StoreContextError as e:
        _log.error(str(e))
        return False

    # Validate the signature of the message itself
    try:
        crypto_certificate = x509.load_pem_x509_certificate(certificate, default_backend())
        crypto_certificate.public_key().verify(
            signature,
            fedmsg.encoding.dumps(message).encode('utf-8'),
            asymmetric.padding.PKCS1v15(),
            hashes.SHA1(),
        )
    except InvalidSignature as e:
        _log.error('message [{m}] has an invalid signature: {e}'.format(
            m=message, e=str(e)))
        return False

    # Step 4, check that the certificate is permitted to emit messages for the
    # topic.
    common_name = crypto_certificate.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)
    common_name = common_name[0]
    routing_policy = config.get('routing_policy', {})
    nitpicky = config.get('routing_nitpicky', False)
    return utils.validate_policy(
        message.get('topic'), common_name.value, routing_policy, nitpicky=nitpicky)


def _validate_signing_cert(ca_certificate, certificate, crl=None):
    """
    Validate an X509 certificate using pyOpenSSL.

    .. note::
        pyOpenSSL is a short-term solution to certificate validation. pyOpenSSL
        is basically in maintenance mode and there's a desire in upstream to move
        all the functionality into cryptography.

    Args:
        ca_certificate (str): A PEM-encoded Certificate Authority certificate to
            validate the ``certificate`` with.
        certificate (str): A PEM-encoded certificate that is in need of validation.
        crl (str): A PEM-encoded Certificate Revocation List which, if provided, will
            be taken into account when validating the certificate.

    Raises:
        X509StoreContextError: If the certificate failed validation. The
            exception contains the details of the error.
    """
    pyopenssl_cert = load_certificate(FILETYPE_PEM, certificate)
    pyopenssl_ca_cert = load_certificate(FILETYPE_PEM, ca_certificate)

    cert_store = X509Store()
    cert_store.add_cert(pyopenssl_ca_cert)
    if crl:
        pyopenssl_crl = load_crl(FILETYPE_PEM, crl)
        cert_store.add_crl(pyopenssl_crl)
        cert_store.set_flags(X509StoreFlags.CRL_CHECK | X509StoreFlags.CRL_CHECK_ALL)

    cert_store_context = X509StoreContext(cert_store, pyopenssl_cert)
    cert_store_context.verify_certificate()
