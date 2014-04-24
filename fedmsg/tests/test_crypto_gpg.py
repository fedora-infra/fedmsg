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
import functools

from nose.tools import raises
from nose.exc import SkipTest

try:
    from nose.tools.nontrivial import make_decorator
except ImportError:
    # It lives here in older versions of nose (el6)
    from nose.tools import make_decorator

import unittest

import fedmsg.crypto.gpg

SEP = os.path.sep
here = SEP.join(__file__.split(SEP)[:-1])

data_dir = SEP.join((here, 'test_certs', 'gpg'))
keyrings = []
clear_data_path = os.path.join(data_dir, "test_data")
secret_fp = 'FBDA 92E4 338D FFD9 EB83  F8F6 3FBD B725 DA19 B4EC'


def skip_on_travis(fn):
    """ A decorator that just skips some tests on travis-ci.org """
    @functools.wraps(fn)
    def newfunc(self, *args, **kw):
        if os.environ.get('TRAVIS', None):
            raise SkipTest("gpg permissions are weird on travis-ci.org")
        return fn(self, *args, **kw)
    return make_decorator(fn)(newfunc)


class TestGpg(unittest.TestCase):
    def setUp(self):
        self.ctx = fedmsg.crypto.gpg.Context(keyrings=keyrings,
                                             homedir=data_dir)

    def test_verif_detach_sig(self):
        signature_path = os.path.join(data_dir, "test_data.sig")
        self.ctx.verify(open(clear_data_path, 'r').read(),
                        signature=open(signature_path, 'rb').read())
        self.ctx.verify_from_file(clear_data_path, sig_path=signature_path)

    @raises(fedmsg.crypto.gpg.GpgBinaryError)
    def test_corrupt_detach_sig(self):
        signature_path = os.path.join(data_dir, "corrupt.sig")
        self.ctx.verify_from_file(clear_data_path, sig_path=signature_path)

    @skip_on_travis
    def test_sign_cleartext(self):
        test_data = u'I can haz a signature?'
        signed_text = self.ctx.clearsign(test_data, fingerprint=secret_fp)
        self.ctx.verify(signed_text)

    @skip_on_travis
    def test_sign_detached(self):
        test_data = u'I can haz a signature?'
        signature = self.ctx.sign(test_data, fingerprint=secret_fp)
        self.ctx.verify(test_data, signature)


import fedmsg.crypto


class TestCryptoGPG(unittest.TestCase):
    def setUp(self):
        gpg_key = 'FBDA 92E4 338D FFD9 EB83  F8F6 3FBD B725 DA19 B4EC'
        self.config = {
            'crypto_backend': 'gpg',
            'gpg_home': SEP.join((here, 'test_certs', 'gpg')),
            'gpg_signing_key': gpg_key
        }

    def tearDown(self):
        self.config = None

    @skip_on_travis
    def test_full_circle(self):
        """ Try to sign and validate a message. """
        message = dict(msg='awesome')
        signed = fedmsg.crypto.sign(message, **self.config)
        assert fedmsg.crypto.validate(signed, **self.config)

    @skip_on_travis
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


if __name__ == '__main__':
    unittest.main()
