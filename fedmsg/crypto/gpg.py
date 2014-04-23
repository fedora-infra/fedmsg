# This file is part of fedmsg.
# Copyright (C) 2013-2014 Simon Chopin <chopin.simon@gmail.com>
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
# Authors:  Simon Chopin <chopin.simon@gmail.com>
#           Ralph Bean <rbean@redhat.com>

import os
import os.path
import tempfile
import shutil
import six
import subprocess

from base64 import b64encode, b64decode

import logging
log = logging.getLogger(__name__)


class GpgBinaryError(Exception):
    pass


class Context(object):
    def __init__(self, keyrings=None, homedir=None):
        self.homedir = homedir or os.path.expanduser(u'~/.gnupg/')
        self.keyrings = keyrings or []

    def _get_keyrings_cl(self, keyrings):
        cl = []
        if keyrings:
            keyrings = self.keyrings + keyrings
        else:
            keyrings = self.keyrings
        for k in keyrings:
            cl.extend(["--keyring", k])
        return cl

    def verify(self, data, signature=None, keyrings=None, homedir=None):
        '''
        `data` <string> the data to verify.
        `signature` <string> The signature, if detached from the data.
        `keyrings` <list of string> Additional keyrings to search in.
        `homedir` <string> Override the configured homedir.
        '''

        if isinstance(data, six.text_type):
            data = data.encode('utf-8')

        tmpdir = tempfile.mkdtemp()
        data_file, data_path = tempfile.mkstemp(dir=tmpdir)
        data_file = os.fdopen(data_file, 'wb')
        data_file.write(data)
        data_file.close()
        if signature:
            sig_file, sig_path = tempfile.mkstemp(dir=tmpdir)
            sig_file = os.fdopen(sig_file, 'wb')
            sig_file.write(signature)
            sig_file.close()
        else:
            sig_path = None
        try:
            return self.verify_from_file(
                data_path,
                sig_path=sig_path,
                keyrings=keyrings,
                homedir=homedir
            )
        finally:
            shutil.rmtree(tmpdir)

    def verify_from_file(self, data_path,
                         sig_path=None, keyrings=None, homedir=None):
        '''
        `data_path` <string> The path to the data to verify.
        `sig_path` <string> The signature file, if detached from the data.
        `keyrings` <list of string> Additional keyrings to search in.
        `homedir` <string> Override the configured homedir.
        '''
        cmd_line = ['gpg', '--homedir', homedir or self.homedir]
        cmd_line.extend(self._get_keyrings_cl(keyrings))

        cmd_line.append('--verify')
        if sig_path:
            cmd_line.extend([sig_path, data_path])
        else:
            cmd_line.append(data_path)

        p = subprocess.Popen(cmd_line, stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode:
            raise GpgBinaryError(stderr)
        return True

    def clearsign(self, data, fingerprint, keyrings=None, homedir=None):

        if isinstance(data, six.text_type):
            data = data.encode('utf-8')

        cmd_line = ['gpg', '--homedir', homedir or self.homedir]
        cmd_line.extend(self._get_keyrings_cl(keyrings))

        cmd_line.extend(['--local-user', fingerprint, '--clearsign'])
        p = subprocess.Popen(
            cmd_line,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(data)
        if p.returncode:
            raise GpgBinaryError(stderr)
        return stdout

    def sign(self, data, fingerprint, keyrings=None, homedir=None):

        if isinstance(data, six.text_type):
            data = data.encode('utf-8')

        cmd_line = ['gpg', '--homedir', homedir or self.homedir]
        cmd_line.extend(self._get_keyrings_cl(keyrings))

        cmd_line.extend(['--local-user', fingerprint, '--detach-sign'])
        p = subprocess.Popen(
            cmd_line,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(data)
        if p.returncode:
            raise GpgBinaryError(stderr)
        return stdout

# Here comes the part actually relevent to fedmsg
""" ``fedmsg.crypto.gpg`` - GnuPG backend for :mod:`fedmsg.crypto` """
import fedmsg.encoding
_ctx = Context()


def sign(message, gpg_home=None, gpg_signing_key=None, **config):
    """ Insert a new field into the message dict and return it.

    The new field is:

        - 'signature' - the computed GPG message digest of the JSON repr
          of the `msg` field.
    """

    if gpg_home is None or gpg_signing_key is None:
        raise ValueError("You must set the gpg_home \
                         and gpg_signing_key keyword arguments.")

    message['crypto'] = 'gpg'

    signature = _ctx.sign(
        fedmsg.encoding.dumps(message['msg']),
        gpg_signing_key,
        homedir=gpg_home
    )
    return dict(list(message.items()) + [('signature', b64encode(signature))])


def validate(message, gpg_home=None, **config):
    """ Return true or false if the message is signed appropriately.

    Two things must be true:

        1) The signature must be valid (obviously)
        2) The signing key must be in the local keyring
           as defined by the `gpg_home` config value.
    """
    if gpg_home is None:
        raise ValueError("You must set the gpg_home keyword argument.")
    try:
        _ctx.verify(
            fedmsg.encoding.dumps(message['msg']),
            b64decode(message['signature']),
            homedir=gpg_home
        )
        return True
    except GpgBinaryError as e:
        log.warn("Failed validation. {0}".format(six.text_type(message)))
        return False
