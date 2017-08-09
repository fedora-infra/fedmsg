# This file is part of fedmsg.
# Copyright (C) 2012 - 2017 Red Hat, Inc.
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
# Authors:  Jeremy Cline <jcline@redhat.com>
import os

import mock
import six

_m2crypto, _cryptography = False, False
try:
    import M2Crypto     # noqa: F401
    import m2ext        # noqa: F401
    _m2crypto = True
except ImportError:
    pass
try:
    import cryptography  # noqa
    import OpenSSL  # noqa
    _cryptography = True
except ImportError:
    pass

try:
    from unittest import skipIf, TestCase, expectedFailure
except ImportError:
    from unittest2 import skipIf, TestCase, expectedFailure

from fedmsg import crypto  # noqa: E402


SSLDIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../test_certs/keys/'))


@skipIf(not (_m2crypto or _cryptography), "Neither M2Crypto nor Cryptography available")
class X509BaseTests(TestCase):

    def setUp(self):
        self.config = {
            'ssldir': SSLDIR,
            'certname': 'shell-app01.phx2.fedoraproject.org',
            'ca_cert_cache': os.path.join(SSLDIR, 'ca.crt'),
            'ca_cert_cache_expiry': 1497618475,  # Stop fedmsg overwriting my CA, See Issue 420

            'crl_location': "http://threebean.org/fedmsg-tests/crl.pem",
            'crl_cache': os.path.join(SSLDIR, 'crl.pem'),
            'crl_cache_expiry': 1497618475,
            'crypto_validate_backends': ['x509'],
        }
        self.sign = crypto.sign
        self.validate = crypto.validate
        crypto._validate_implementations = None

    def test_missing_certname(self):
        """Assert a missing certname argument results in a ValueError."""
        self.config.pop('certname')
        with self.assertRaises(ValueError):
            self.sign({'my': 'message'}, **self.config)

    def test_missing_ssldir(self):
        """Assert a missing ssldir argument results in a ValueError."""
        self.config.pop('ssldir')
        with self.assertRaises(ValueError):
            self.sign({'my': 'message'}, **self.config)

    def test_sign(self):
        """Assert signing a message inserts the certificate and a signature."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.assertTrue('signature' in signed)
        self.assertTrue('certificate' in signed)

    @expectedFailure
    def test_signature_text(self):
        """Assert signature fields are unicode text."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.assertTrue(isinstance(signed['signature'], six.text_type))

    @expectedFailure
    def test_certificate_text(self):
        """Assert signing a message inserts the certificate and a signature."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.assertTrue(isinstance(signed['certificate'], six.text_type))

    def test_sign_and_verify(self):
        """Assert signed messages are verified."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.assertTrue(self.validate(signed, **self.config))

    def test_unsigned(self):
        """Assert unsigned messages are *not* verified."""
        self.assertFalse(self.validate({'my': 'message'}, **self.config))

    def test_invalid_ca(self):
        """Assert when the CA didn't sign the certificate, validation fails."""
        self.config['ca_cert_cache'] = os.path.join(SSLDIR, 'badca.crt')

        signed = self.sign({'my': 'message'}, **self.config)
        self.assertFalse(self.validate(signed, **self.config))

    def test_invalid_signing_cert(self):
        """Assert when the certificate didn't sign the message, validation fails."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.config['certname'] = 'shell-app02.phx2.fedoraproject.org'
        other_signed = self.sign({'my': 'message'}, **self.config)

        signed['certificate'] = other_signed['certificate']

        self.assertFalse(self.validate(signed, **self.config))

    def test_signed_by_revoked_cert(self):
        """Assert when the certificate has been revoked, validation fails."""
        self.config['certname'] = 'dummy-revoked'
        signed = self.sign({'my': 'message'}, **self.config)

        self.assertFalse(self.validate(signed, **self.config))

    def test_invalid_message_signature(self):
        """Assert when the signed digest doesn't match the message digest, validation fails."""
        signed = self.sign({'message': 'so secure'}, **self.config)
        signed['message'] = 'so insecure!'
        self.assertFalse(self.validate(signed, **self.config))

    def test_no_crl(self):
        """Assert that it's okay to not use a CRL."""
        del self.config['crl_location']
        del self.config['crl_cache']
        del self.config['crl_cache_expiry']

        signed = self.sign({'message': 'so secure'}, **self.config)
        self.assertTrue(self.validate(signed, **self.config))

    def test_signed_by_expired_ca(self):
        """Assert certs signed by an expired CA fail validation."""
        self.config['certname'] = 'signed_by_expired_ca'
        self.config['ca_cert_cache'] = os.path.join(SSLDIR, 'expired_ca.crt')
        # There's no CRL for this CA.
        del self.config['crl_location']
        del self.config['crl_cache']
        del self.config['crl_cache_expiry']

        signed = self.sign({'message': 'so secure'}, **self.config)
        self.assertFalse(self.validate(signed, **self.config))

    def test_invalid_policy(self):
        """Assert when the policy is invalid, False is returned."""
        self.config['routing_policy'] = {'mytopic': ['Not shell-app01.phx2.fedoraproject.org']}
        self.config['routing_nitpicky'] = True
        signed = self.sign({'topic': 'mytopic', 'message': 'so secure'}, **self.config)
        self.assertFalse(self.validate(signed, **self.config))

    def test_valid_policy(self):
        """Assert when the policy is valid, True is returned."""
        self.config['routing_policy'] = {'mytopic': ['shell-app01.phx2.fedoraproject.org']}
        self.config['routing_nitpicky'] = True
        signed = self.sign({'topic': 'mytopic', 'message': 'so secure'}, **self.config)
        self.assertTrue(self.validate(signed, **self.config))

    def test_bytes_undecodable(self):
        """Assert un-decodable signatures/certificates fails validation."""
        signed = self.sign({'topic': 'mytopic', 'message': 'so secure'}, **self.config)

        # This assertion will fail when the sign API changes to return text types, at
        # which point this test should encode the signature to bytes.
        self.assertTrue(isinstance(signed['signature'], six.binary_type))
        self.assertTrue(isinstance(signed['certificate'], six.binary_type))

        # This is a non-ascii character that encodes to a bytestring in latin-1
        # that won't decode in UTF-8
        signed['signature'] = u'Ö'.encode('latin-1')
        signed['certificate'] = u'Ö'.encode('latin-1')

        self.assertFalse(self.validate(signed, **self.config))


@skipIf(not _cryptography, "cryptography/pyOpenSSL are missing.")
class X509CryptographyTests(X509BaseTests):
    """Tests that explicitly use the cryptography-based sign/verify."""

    def setUp(self):
        super(X509CryptographyTests, self).setUp()
        self.sign = crypto.x509_ng.sign
        self.validate = crypto.x509_ng.validate

    def test_old_crl(self):
        """Assert when an old CRL is used, validation fails."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.config['crl_cache'] = os.path.join(SSLDIR, 'expired_crl.pem')

        self.assertFalse(self.validate(signed, **self.config))

    @mock.patch('fedmsg.crypto.x509_ng._log')
    def test_bytes_logs_error(self, mock_log):
        """Assert calling validate with byte signature/certificate logs an error."""
        signed = self.sign({'topic': 'mytopic', 'message': 'so secure'}, **self.config)

        # This assertion will fail when the sign API changes to return text types, at
        # which point this test should encode the signature to bytes.
        self.assertTrue(isinstance(signed['signature'], six.binary_type))
        self.assertTrue(isinstance(signed['certificate'], six.binary_type))

        self.assertTrue(self.validate(signed, **self.config))
        mock_log.error.assert_any_call("msg['signature'] is not a unicode string")
        mock_log.error.assert_any_call("msg['certificate'] is not a unicode string")


@skipIf(not _m2crypto, "M2Crypto/m2ext are missing.")
class X509M2CryptoTests(X509BaseTests):
    """Tests that explicitly use the m2crypto-based sign/verify."""

    def setUp(self):
        super(X509M2CryptoTests, self).setUp()
        self.sign = crypto.x509._m2crypto_sign
        self.validate = crypto.x509._m2crypto_validate

    @expectedFailure
    def test_old_crl(self):
        """Assert when an old CRL is used, validation fails."""
        signed = self.sign({'my': 'message'}, **self.config)
        self.config['crl_cache'] = os.path.join(SSLDIR, 'expired_crl.pem')

        self.assertFalse(self.validate(signed, **self.config))

    @mock.patch('fedmsg.crypto.x509._log')
    def test_bytes_logs_error(self, mock_log):
        """Assert calling validate with byte signature/certificate logs an error."""
        signed = self.sign({'topic': 'mytopic', 'message': 'so secure'}, **self.config)

        # This assertion will fail when the sign API changes to return text types, at
        # which point this test should encode the signature to bytes.
        self.assertTrue(isinstance(signed['signature'], six.binary_type))
        self.assertTrue(isinstance(signed['certificate'], six.binary_type))

        self.assertTrue(self.validate(signed, **self.config))
        mock_log.error.assert_any_call("msg['signature'] is not a unicode string")
        mock_log.error.assert_any_call("msg['certificate'] is not a unicode string")


@skipIf(not (_cryptography and _m2crypto), 'M2Crypto and cryptography required.')
class M2CryptoWithCryptoTests(X509BaseTests):
    """Tests that use m2crypto for signing and validate with cryptography."""

    def setUp(self):
        super(M2CryptoWithCryptoTests, self).setUp()
        self.sign = crypto.x509._m2crypto_sign
        self.validate = crypto.x509._crypto_validate


@skipIf(not (_cryptography and _m2crypto), 'M2Crypto and cryptography required.')
class CryptoWithM2CryptoTests(X509BaseTests):
    """Tests that use cryptography for signing and validate with m2crypto."""

    def setUp(self):
        super(CryptoWithM2CryptoTests, self).setUp()
        self.sign = crypto.x509._crypto_sign
        self.validate = crypto.x509._m2crypto_validate


@skipIf(not (_cryptography and _m2crypto), 'M2Crypto and cryptography required.')
class CompatibleFormatTests(TestCase):
    """Tests that use cryptography for signing and validate with m2crypto."""

    def setUp(self):
        self.config = {
            'ssldir': SSLDIR,
            'certname': 'shell-app01.phx2.fedoraproject.org',
            'ca_cert_cache': os.path.join(SSLDIR, 'ca.crt'),
            'ca_cert_cache_expiry': 1497618475,  # Stop fedmsg overwriting my CA, See Issue 420

            'crl_location': "http://threebean.org/fedmsg-tests/crl.pem",
            'crl_cache': os.path.join(SSLDIR, 'crl.pem'),
            'crl_cache_expiry': 1497618475,
            'crypto_validate_backends': ['x509'],
        }

    def test_sign(self):
        """Assert signed messages are identical with cryptography and m2crypto."""
        crypto_signed = crypto.x509._crypto_sign({'my': 'message'}, **self.config)
        m2crypto_signed = crypto.x509._m2crypto_sign({'my': 'message'}, **self.config)

        self.assertDictEqual(crypto_signed, m2crypto_signed)
