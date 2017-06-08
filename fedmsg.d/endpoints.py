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
config = dict(
    # This is a dict of possible addresses from which fedmsg can send
    # messages.  fedmsg.init(...) requires that a 'name' argument be passed
    # to it which corresponds with one of the keys in this dict.
    endpoints={
        # These are here so your local box can listen to the upstream
        # infrastructure's bus.  Cool, right?  :)
        "fedora-infrastructure": [
            "tcp://hub.fedoraproject.org:9940",
            # "tcp://stg.fedoraproject.org:9940",
        ],
        # "debian-infrastructure": [
        #    "tcp://fedmsg.olasd.eu:9940",
        # ],
        # "anitya-public-relay": [
        #    "tcp://release-monitoring.org:9940",
        # ],
    },
)
