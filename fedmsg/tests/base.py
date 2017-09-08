import os
import unittest

import vcr

#: The directory where test fixtures should be placed.
FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fixtures/'))

#: The directory where all the test x509 certificates are stored.
SSLDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test_certs/keys/'))


class FedmsgTestCase(unittest.TestCase):
    """Base test case that does useful setup/teardown for all fedmsg tests."""

    def setUp(self):
        """
        Set up the test environment.

        VCR is set up for all tests using the FIXTURES_DIR to store the recordings.

        .. note:: VCR is set to ``record_mode='none'`` so tests fail if a real request
            is made. This is helpful to ensure tests always use the recording, but you
            will need to set it to ``record_mode='once'`` when a new recording is
            required.
        """
        my_vcr = vcr.VCR(
            cassette_library_dir=os.path.join(FIXTURES_DIR, 'vcr'), record_mode='none')
        self.vcr = my_vcr.use_cassette(self.id())
        self.vcr.__enter__()
        self.addCleanup(self.vcr.__exit__, None, None, None)
