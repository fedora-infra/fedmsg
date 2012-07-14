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
        # In prod/stg, map hostname to the name of the cert in ssldir.
        # Unfortunately, we can't use socket.getfqdn()
        #"app01.stg": "app01.stg.phx2.fedoraproject.org",
        "bodhi.%s" % hostname: "test_cert",
        "fas.%s" % hostname: "test_cert",
        "fedoratagger.%s" % hostname: "test_cert",
        "mediawiki.%s" % hostname: "test_cert",
        "pkgdb.%s" % hostname: "test_cert",
        "busmon.%s" % hostname: "test_cert",
    },
)
