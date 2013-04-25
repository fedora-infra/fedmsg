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

from nose.tools import raises
import unittest

import fedmsg.crypto

SEP = os.path.sep
here = SEP.join(__file__.split(SEP)[:-1])


class TestCryptoGPG(unittest.TestCase):

    def setUp(self):
        self.config = {
            'crypto_backend': 'gpg',
            'ssldir': SEP.join((here, 'test_certs/keys_gpg')),
            'certname': 'TODO -- fill me in.'
        }

    def tearDown(self):
        self.config = None

    @raises(NotImplementedError)
    def test_full_circle(self):
        """ Try to sign and validate a message. """
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        assert fedmsg.crypto.validate(signed, **self.config)

    @raises(NotImplementedError)
    def test_failed_validation(self):
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        # space aliens read data off the wire and inject incorrect data
        signed['msg'] = "eve wuz here"
        assert not fedmsg.crypto.validate(signed, **self.config)


if __name__ == '__main__':
    unittest.main()
