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
import os

try:
    # For python-2.6, so we can do skipTest
    import unittest2 as unittest
except ImportError:
    import unittest

import fedmsg.crypto

SEP = os.path.sep
here = SEP.join(__file__.split(SEP)[:-1])

def skip_if_missing_libs(f):
    def _wrapper(self, *args, **kw):
        try:
            import M2Crypto
            import m2ext
        except ImportError, e:
            self.skipTest(str(e))

        return f(self, *args, **kw)

    return _wrapper

class TestCrypto(unittest.TestCase):

    def setUp(self):
        self.config = {
            # Normally this is /var/lib/puppet/ssl
            'ssldir': SEP.join((here, 'test_certs/keys')),
            # Normally this is 'app01.stg.phx2.fedoraproject.org'
            'certname': 'shell-app01.phx2.fedoraproject.org',
            'crl_location': "http://threebean.org/fedmsg-tests/crl.pem",
            'crl_cache': "/tmp/crl.pem",
            'crl_cache_expiry': 10,

        }

    def tearDown(self):
        self.config = None

    @skip_if_missing_libs
    def test_full_circle(self):
        """ Try to sign and validate a message. """
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        assert fedmsg.crypto.validate(signed, **self.config)

    @skip_if_missing_libs
    def test_failed_validation(self):
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        # space aliens read data off the wire and inject incorrect data
        signed['msg'] = "eve wuz here"
        assert not fedmsg.crypto.validate(signed, **self.config)


if __name__ == '__main__':
    unittest.main()
