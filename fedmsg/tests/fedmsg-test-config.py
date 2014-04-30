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
""" Test config. """
import os
import socket
import random

SEP = os.path.sep
here = os.getcwd()
hostname = socket.gethostname().split('.', 1)[0]

ssl_enabled_for_tests = True
try:
    import M2Crypto
    import m2ext
except ImportError:
    ssl_enabled_for_tests = False

# Pick random ports for the tests so travis-ci doesn't flip out.
port = random.randint(4000, 20000)

gpg_key_unittest = 'FBDA 92E4 338D FFD9 EB83  F8F6 3FBD B725 DA19 B4EC'
gpg_key_main = 'FBDA 92E4 338D FFD9 EB83  F8F6 3FBD B725 DA19 B4EC'

config = dict(
    topic_prefix="com.test_prefix",
    endpoints={
        "unittest.%s" % hostname: [
            "tcp://*:%i" % (port + 1),
            "tcp://*:%i" % (port + 2),
        ],
        "twisted.%s" % hostname: [
            "tcp://*:%i" % (port + 3),
        ],
        "__main__.%s" % hostname: [
            "tcp://*:%i" % (port + 4),
            "tcp://*:%i" % (port + 5),
            "tcp://*:%i" % (port + 6),
            "tcp://*:%i" % (port + 7),
            "tcp://*:%i" % (port + 8),
            "tcp://*:%i" % (port + 9),
        ],
        "unittest2.%s" % hostname: [
            "tcp://*:%i" % (port + 10),
            "tcp://*:%i" % (port + 11),
        ],
        # Guarantee that we don't fall over with a bogus endpoint.
        "blah.%s": "tcp://www.flugle.horn:88",
    },
    relay_inbound=["tcp://127.0.0.1:%i" % (port - 1)],
    replay_endpoints={
        'unittest.%s' % hostname: "tcp://127.0.0.1:%i" % (port + 1),
        'unittest2.%s' % hostname: "tcp://127.0.0.1:%i" % (port + 2),
    },
    persistent_store=None,
    environment="dev",
    high_water_mark=0,
    io_threads=1,
    irc=[],
    zmq_enabled=True,
    zmq_strict=False,

    zmq_reconnect_ivl=100,
    zmq_reconnect_ivl_max=1000,

    # SSL stuff.
    sign_messages=ssl_enabled_for_tests,
    validate_signatures=ssl_enabled_for_tests,
    ssldir=SEP.join([here, 'test_certs/keys']),

    crl_location="http://threebean.org/fedmsg-tests/crl.pem",
    crl_cache="/tmp/crl.pem",
    crl_cache_expiry=10,

    certnames={
        "unittest.%s" % hostname: "shell-app01.phx2.fedoraproject.org",
        "unittest2.%s" % hostname: "shell-app01.phx2.fedoraproject.org",
        "__main__.%s" % hostname: "shell-app01.phx2.fedoraproject.org",
        # In prod/stg, map hostname to the name of the cert in ssldir.
        # Unfortunately, we can't use socket.getfqdn()
        #"app01.stg": "app01.stg.phx2.fedoraproject.org",
    },
    gpg_keys={
        "unittest.%s" % hostname: gpg_key_unittest,
        "unittest2.%s" % hostname: gpg_key_unittest,
        "__main__.%s" % hostname: gpg_key_main,
    }
)
