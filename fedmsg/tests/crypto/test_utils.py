import os
import shutil
import tempfile
import unittest

# In Python 3 the mock is part of unittest
try:
    import mock
except ImportError:
    from unittest import mock

from fedmsg.crypto import utils
from fedmsg.tests import base


class FixDatanommerMessageTests(unittest.TestCase):
    """Tests for the :func:`fedmsg.crypto.utils.fix_datagrepper_message` function."""

    def test_no_source_keys(self):
        """Assert messages with neither "source_name" or "source_version" are untouched."""
        original_message = {'my': 'message'}

        self.assertTrue(original_message is utils.fix_datagrepper_message(original_message))

    def test_no_source_version(self):
        """Assert messages missing the "source_version" key are untouched."""
        original_message = {'source_version': '0.1.0'}

        self.assertTrue(original_message is utils.fix_datagrepper_message(original_message))

    def test_no_source_name(self):
        """Assert messages missing the "source_name" key are untouched."""
        original_message = {'source_name': 'datanommer'}

        self.assertTrue(original_message is utils.fix_datagrepper_message(original_message))

    def test_no_timestamp(self):
        """Assert messages missing the 'timestamp' key are handled correctly."""
        original_message = {
            'source_name': 'datanommer',
            'source_version': '1',
        }

        self.assertEqual({}, utils.fix_datagrepper_message(original_message))

    def test_float_timestamp(self):
        """Assert the "timestamp" key is converted to an int from a float."""
        original_message = {
            'source_name': 'datanommer',
            'source_version': '1',
            'timestamp': 1.0,
        }

        self.assertEqual({'timestamp': 1}, utils.fix_datagrepper_message(original_message))

    def test_empty_headers(self):
        """Assert the "headers" key is removed if it is empty."""
        original_message = {
            'source_name': 'datanommer',
            'source_version': '1',
            'headers': {},
        }

        self.assertEqual({}, utils.fix_datagrepper_message(original_message))

    def test_headers(self):
        """Assert the "headers" key is untouched if it has a value."""
        original_message = {
            'source_name': 'datanommer',
            'source_version': '1',
            'headers': {'k': 'v'},
        }

        self.assertEqual({'headers': {'k': 'v'}}, utils.fix_datagrepper_message(original_message))

    def test_message_copied(self):
        """Assert messages are copied if they are altered."""
        original_message = {'source_name': 'datanommer', 'source_version': '1'}

        self.assertEqual({}, utils.fix_datagrepper_message(original_message))
        self.assertEqual({'source_name': 'datanommer', 'source_version': '1'}, original_message)


class ValidatePolicyTests(unittest.TestCase):
    """Tests for :func:`utils.validate_policy`."""

    def test_signer_in_routing_policy_topic(self):
        """Assert when the signer is in the routing policy, ``True`` is returned."""
        result = utils.validate_policy('mytopic', 'MySignerCN', {'mytopic': ['MySignerCN']})
        self.assertTrue(result)

    def test_signer_not_in_routing_policy_topic(self):
        """Assert when the signer is in the routing policy, ``True`` is returned."""
        policy = {'mytopic': ['OtherSigner'], 'othertopic': ['MySignerCN']}
        result = utils.validate_policy('mytopic', 'MySignerCN', policy)
        self.assertFalse(result)

    def test_topic_missing_nitpicky(self):
        """Assert when the topic isn't in the policy at all, False is returned with nitpicky."""
        policy = {'othertopic': ['MySignerCN']}
        result = utils.validate_policy('mytopic', 'MySignerCN', policy, nitpicky=True)
        self.assertFalse(result)

    def test_topic_missing_not_nitpicky(self):
        """Assert when the topic isn't in the policy at all, True is returned without nitpicky."""
        policy = {'othertopic': ['MySignerCN']}
        result = utils.validate_policy('mytopic', 'MySignerCN', policy, nitpicky=False)
        self.assertTrue(result)


class LoadCertificateTests(base.FedmsgTestCase):
    """Tests for :func:`utils._load_remote_cert`."""

    def setUp(self):
        super(LoadCertificateTests, self).setUp()

        self.cache_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.cache_dir, 'ca.crt')
        self.addCleanup(shutil.rmtree, self.cache_dir, True)

    def test_remote_cert(self):
        """Assert requesting a remote certificate works and is cached."""
        location = 'https://fedoraproject.org/fedmsg/ca.crt'
        with open(os.path.join(base.SSLDIR, 'fedora_ca.crt'), 'r') as fd:
            expected_cert = fd.read()

        with mock.patch.dict('fedmsg.crypto.utils._cached_certificates', clear=True):
            ca, crl = utils.load_certificates(location)
            self.assertEqual((str(expected_cert), None), utils._cached_certificates[location])
        self.assertEqual(expected_cert, ca)
        self.assertTrue(crl is None)

    @mock.patch('fedmsg.crypto.utils._load_certificate')
    def test_valid_cache(self, mock_load_cert):
        """Assert when the cache is present it is used."""
        location = '/crt'

        with mock.patch.dict('fedmsg.crypto.utils._cached_certificates', {'/crt': ('crt', None)}):
            ca, crl = utils.load_certificates(location)
        self.assertEqual('crt', ca)
        self.assertTrue(crl is None)
        self.assertEqual(0, mock_load_cert.call_count)

    @mock.patch('fedmsg.crypto.utils._load_certificate')
    def test_invalidate_cache(self, mock_load_cert):
        """Assert when the cache is present it is used."""
        location = '/crt'
        mock_load_cert.return_value = 'fresh_ca'

        with mock.patch.dict('fedmsg.crypto.utils._cached_certificates', {'/crt': ('crt', None)}):
            ca, crl = utils.load_certificates(location, invalidate_cache=True)
            self.assertEqual(('fresh_ca', None), utils._cached_certificates[location])
        self.assertEqual('fresh_ca', ca)
        self.assertTrue(crl is None)
        mock_load_cert.assert_called_once_with('/crt')
