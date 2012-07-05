import os
import unittest

import fedmsg.crypto

SEP = os.path.sep
here = SEP.join(__file__.split(SEP)[:-1])


class TestCrypto(unittest.TestCase):

    def setUp(self):
        self.config = {
            # Normally this is /var/lib/puppet/ssl
            'ssldir': SEP.join((here, 'test_certs')),
            # Normally this is 'app01.stg.phx2.fedoraproject.org'
            'certname': 'test_cert',
        }
        try:
            import M2Crypto
            import m2ext
        except ImportError, e:
            self.skipTest(str(e))

    def tearDown(self):
        self.config = None

    def test_full_circle(self):
        """ Try to sign and validate a message. """
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        assert fedmsg.crypto.validate(signed, **self.config)

    def test_failed_validation(self):
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        # space aliens read data off the wire and inject incorrect data
        signed['msg'] = "eve wuz here"
        assert not fedmsg.crypto.validate(signed, **self.config)


if __name__ == '__main__':
    unittest.main()
