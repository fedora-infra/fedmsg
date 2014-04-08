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
import os
import socket

SEP = os.path.sep
here = os.getcwd()

config = dict(
    sign_messages=False,
    validate_signatures=True,

    # Use these implementations to sign and validate messages
    crypto_backend='x509',
    crypto_validate_backends=['x509'],

    ssldir="/etc/pki/fedmsg",
    crl_location="https://fedoraproject.org/fedmsg/crl.pem",
    crl_cache="/var/run/fedmsg/crl.pem",
    crl_cache_expiry=10,

    ca_cert_location="https://fedoraproject.org/fedmsg/ca.crt",
    ca_cert_cache="/var/run/fedmsg/ca.crt",
    ca_cert_cache_expiry=0,  # Never expires

    certnames={
        # In prod/stg, map hostname to the name of the cert in ssldir.
        # Unfortunately, we can't use socket.getfqdn()
        #"app01.stg": "app01.stg.phx2.fedoraproject.org",
    },

    # A mapping of fully qualified topics to a list of cert names for which
    # a valid signature is to be considered authorized.  Messages on topics not
    # listed here are considered automatically authorized.
    routing_policy={
        # Only allow announcements from production if they're signed by a
        # certain certificate.
        "org.fedoraproject.prod.announce.announcement": [
            "announce-lockbox.phx2.fedoraproject.org",
        ],
    },

    # Set this to True if you want messages to be dropped that aren't
    # explicitly whitelisted in the routing_policy.
    # When this is False, only messages that have a topic in the routing_policy
    # but whose cert names aren't in the associated list are dropped; messages
    # whose topics do not appear in the routing_policy are not dropped.
    routing_nitpicky=False,
)
