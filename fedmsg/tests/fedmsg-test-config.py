""" Test config. """
import os
import socket
import random

SEP = os.path.sep
here = os.getcwd()
hostname = socket.gethostname()

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
    },
    relay_inbound="tcp://127.0.0.1:%i" % (port - 1),
    environment="dev",
    high_water_mark=0,
    io_threads=1,
    irc=[],
    zmq_enabled=True,
    zmq_strict=False,

    # SSL stuff.
    sign_messages=True,
    validate_signatures=True,
    ssldir=SEP.join([here, 'dev_certs']),

    certnames={
        hostname: "test_cert",
        # In prod/stg, map hostname to the name of the cert in ssldir.
        # Unfortunately, we can't use socket.getfqdn()
        #"app01.stg": "app01.stg.phx2.fedoraproject.org",
    },
)
