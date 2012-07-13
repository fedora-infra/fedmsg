import os
import socket

SEP = os.path.sep
here = os.getcwd()
hostname = socket.gethostname()

config = dict(
    sign_messages=False,
    validate_signatures=False,
    ssldir=SEP.join([here, 'dev_certs']),

    certnames={
        hostname: "test_cert",
        # In prod/stg, map hostname to the name of the cert in ssldir.
        # Unfortunately, we can't use socket.getfqdn()
        #"app01.stg": "app01.stg.phx2.fedoraproject.org",
    },
)
