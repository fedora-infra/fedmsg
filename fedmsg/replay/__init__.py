# This file is part of fedmsg
# Copyright (C) 2013 Simon Chopin <chopin.simon@gmail.com>
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
#

import fedmsg.encoding
import fedmsg.utils

import socket

import zmq

class ReplayContext(object):
    def __init__(self, **config):
        '''
        The socket must be of zmq.REP type, and be already bound to an endpoint.
        It is assumed it will not be shared, the socket closing will occur in
        this thread.
        '''
        self.config = config

        if not config.get('persistent_store', None):
            raise ValueError("No valid persistent_store config value found.")
        self.store = config['persistent_store']

        self.hostname = socket.gethostname().split('.', 1)[0]
        if not config.get("name", None):
            module_name = fedmsg.utils.guess_calling_module(default="fedmsg")
            config["name"] = module_name + '.' + self.hostname

        self.context = zmq.Context(config['io_threads'])
        self.publisher = self.context.socket(zmq.REP)

        # If there's a Key error, let if fail.
        endpoint = "tcp://*:{port}".format(
            port=config['replay_endpoints'][config['name']].rsplit(':')[-1]
        )
        try:
            self.publisher.bind(endpoint)
            fedmsg.utils.set_high_water_mark(self.publisher, self.config)
            fedmsg.utils.set_tcp_keepalive(self.publisher, self.config)
        except zmq.ZMQError:
            raise IOError("The replay endpoint cannot be bound.")

    # Put this in a separate method to ease testing.
    def _req_rep_cycle(self):
        res = self.publisher.poll()
        if res > 0:
            query = fedmsg.encoding.loads(self.publisher.recv())
            try:
                self.publisher.send_multipart(
                        [fedmsg.encoding.dumps(m) for m in self.store.get(query)]
                    )
            except ValueError as e:
                self.publisher.send("error: '{}'".format(e.message))

    def listen(self):
        try:
            while True:
                self._req_rep_cycle()
        finally:
            self.publisher.close()

