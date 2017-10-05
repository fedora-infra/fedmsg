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
import stat

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import fedmsg.crypto
import fedmsg.crypto.gpg

SEP = os.path.sep
here = SEP.join(__file__.split(SEP)[:-1])

data_dir = SEP.join((here, 'test_certs', 'gpg'))
clear_data_path = os.path.join(data_dir, "test_data")
# Older versions of GPG don't handle the full key digest, so we will use the
# short one for the moment.
secret_fp = 'DA19B4EC'


class TestGpg(unittest.TestCase):
    def setUp(self):
        # Equivalent to chmod 700. If the directory isn't protected, GPG gets unhappy.
        os.chmod(data_dir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | 0)
        for root, __, files in os.walk(data_dir):
            for f in files:
                os.chmod(os.path.join(root, f), stat.S_IRUSR | stat.S_IWUSR | 0)

        self.ctx = fedmsg.crypto.gpg.Context(homedir=data_dir)

    def test_verif_detach_sig(self):
        signature_path = os.path.join(data_dir, "test_data.sig")
        self.ctx.verify(open(clear_data_path, 'r').read(),
                        signature=open(signature_path, 'rb').read())
        self.ctx.verify_from_file(clear_data_path, sig_path=signature_path)

    def test_corrupt_detach_sig(self):
        with self.assertRaises(fedmsg.crypto.gpg.GpgBinaryError):
            signature_path = os.path.join(data_dir, "corrupt.sig")
            self.ctx.verify_from_file(clear_data_path, sig_path=signature_path)

    def test_sign_cleartext(self):
        test_data = u'I can haz a signature?'
        signed_text = self.ctx.clearsign(test_data, fingerprint=secret_fp)
        self.ctx.verify(signed_text)

    def test_sign_detached(self):
        test_data = u'I can haz a signature?'
        signature = self.ctx.sign(test_data, fingerprint=secret_fp)
        self.ctx.verify(test_data, signature)


class TestCryptoGPG(unittest.TestCase):
    def setUp(self):
        self.config = {
            'crypto_backend': 'gpg',
            'gpg_home': SEP.join((here, 'test_certs', 'gpg')),
            'gpg_signing_key': secret_fp
        }

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

    def tearDown(self):
        # We have to reset the implementation in fedmsg.crypto
        # otherwise all the other tests will use the gpg backend
        fedmsg.crypto._implementation = None
        self.config = None


if __name__ == '__main__':
    unittest.main()
