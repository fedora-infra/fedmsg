import os
import time
import unittest

import mock

from fedmsg.crypto import utils


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


class LoadRemoteCertTests(unittest.TestCase):
    """Tests for :func:`utils._load_remote_cert`."""

    @mock.patch('fedmsg.crypto.utils.os.stat')
    def test_valid_cache(self, mock_stat):
        """Assert when the primary cache is valid it's used."""
        mock_stat.return_value.st_mtime = time.time()
        cache = utils._load_remote_cert('https://example.com/ca.crt', '/my/ca.crt', 60)

        self.assertEqual('/my/ca.crt', cache)
        mock_stat.assert_called_once_with('/my/ca.crt')

    @mock.patch('fedmsg.crypto.utils.os.stat')
    def test_valid_alternate_cache(self, mock_stat):
        """Assert when the alternate cache is valid it's used."""
        mock_stat.side_effect = [OSError, mock.Mock(st_mtime=time.time())]
        cache = utils._load_remote_cert('https://example.com/ca.crt', '/my/ca.crt', 60)

        self.assertEqual(os.path.expanduser('~/.local/my/ca.crt'), cache)
        self.assertEqual('/my/ca.crt', mock_stat.call_args_list[0][0][0])
        self.assertEqual(
            os.path.expanduser('~/.local/my/ca.crt'), mock_stat.call_args_list[1][0][0])
