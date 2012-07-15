""" Test config. """
import os
import socket
import random

SEP = os.path.sep
here = os.getcwd()
hostname = socket.gethostname()

ssl_enabled_for_tests = True
try:
    import M2Crypto
    import m2ext
except ImportError:
    ssl_enabled_for_tests = False

# Pick random ports for the tests so travis-ci doesn't flip out.
port = random.randint(4000, 20000)

config = dict(
    endpoints={
        "unittest.%s" % hostname: [
            "tcp://*:%i" % (port + 1),
            "tcp://*:%i" % (port + 2),
        ],
        "twisted.%s" % hostname: [
            "tcp://*:%i" % (port + 3),
        ],
        "blah.%s": [
            # Guarantee that we don't fall over with a bogus endpoint.
            "tcp://www.flugle.horn:88",
        ]
    },
    relay_inbound="tcp://127.0.0.1:%i" % (port - 1),
    environment="dev",
    high_water_mark=0,
    io_threads=1,
    irc=[],
    zmq_enabled=True,
    zmq_strict=False,

    # SSL stuff.
    sign_messages=ssl_enabled_for_tests,
    validate_signatures=ssl_enabled_for_tests,
    ssldir=SEP.join([here, 'dev_certs/keys']),

    certnames={
        "unittest.%s" % hostname: "shell-app01.phx2.fedoraproject.org",
        # In prod/stg, map hostname to the name of the cert in ssldir.
        # Unfortunately, we can't use socket.getfqdn()
        #"app01.stg": "app01.stg.phx2.fedoraproject.org",
    },
)
