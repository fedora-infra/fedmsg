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
    # Set this to dev if you're hacking on fedmsg or an app.
    # Set to stg or prod if running in the Fedora Infrastructure
    environment="dev",

    # Default is 0
    high_water_mark=0,
    io_threads=1,

    ## For the fedmsg-hub and fedmsg-relay. ##

    # We almost always want the fedmsg-hub to be sending messages with zmq as
    # opposed to amqp or stomp.
    zmq_enabled=True,

    # When subscribing to messages, we want to allow splats ('*') so we tell
    # the hub to not be strict when comparing messages topics to subscription
    # topics.
    zmq_strict=False,

    # Number of seconds to sleep after initializing waiting for sockets to sync
    post_init_sleep=0.5,

    # Wait a whole second to kill all the last io threads for messages to
    # exit our outgoing queue (if we have any).  This is in milliseconds.
    zmq_linger=1000,

    # See the following
    #   - http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/overview.html
    #   - http://api.zeromq.org/3-2:zmq-setsockopt
    zmq_tcp_keepalive=1,
    zmq_tcp_keepalive_cnt=3,
    zmq_tcp_keepalive_idle=60,
    zmq_tcp_keepalive_intvl=5,
)
