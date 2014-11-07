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
import six
import sys
import os

import nose.tools.nontrivial

major, minor = sys.version_info[:2]
if major == 2 and minor <= 6:
    # For python-2.6, so we can do skipTest
    import unittest2 as unittest
else:
    import unittest

import fedmsg.crypto

SEP = os.path.sep
here = SEP.join(__file__.split(SEP)[:-1])


def skip_if_missing_x509_libs(f):
    def _wrapper(self, *args, **kw):
        try:
            import M2Crypto
            import m2ext
        except ImportError as e:
            self.skipTest(six.text_type(e))

        return f(self, *args, **kw)

    return nose.tools.nontrivial.make_decorator(f)(_wrapper)


class TestCryptoSwitching(unittest.TestCase):

    def setUp(self):
        self.config = {
            # Normally this is /var/lib/puppet/ssl
            'ssldir': SEP.join((here, 'test_certs/keys')),
            # Normally this is 'app01.stg.phx2.fedoraproject.org'
            'certname': 'shell-app01.phx2.fedoraproject.org',
            'crl_location': "http://threebean.org/fedmsg-tests/crl.pem",
            'crl_cache': "/tmp/crl.pem",
            'crl_cache_expiry': 10,

            # But *not* x509
            'crypto_validate_backends': ['gpg'],
        }
        # Need to reset this global
        fedmsg.crypto._validate_implementations = None

    def tearDown(self):
        self.config = None
        # Need to reset this global
        fedmsg.crypto._validate_implementations = None

    @skip_if_missing_x509_libs
    def test_invalid_validator(self):
        """ Try to verify an x509 message when only gpg is allowed. """
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        assert not fedmsg.crypto.validate(signed, **self.config)


if __name__ == '__main__':
    unittest.main()
