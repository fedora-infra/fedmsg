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
#           Ralph Bean <rbean@redhat.com>
#

import six
import fedmsg.encoding
import fedmsg.utils

import socket

import zmq


class ReplayContext(object):
    def __init__(self, **config):
        '''
        This will initiate a Context that just waits for clients to connect
        and proxies their queries to the store and back.
        To start the listening, use the listen() method.
        '''
        self.config = config

        # No point of a replay context without message store
        if not config.get('persistent_store', None):
            raise ValueError("No valid persistent_store config value found.")
        self.store = config['persistent_store']

        self.hostname = socket.gethostname().split('.', 1)[0]
        if not config.get("name", None):
            # Try to guess an appropriate name
            # It is however probably better if the name is explicitly defined.
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
        res = self.publisher.poll(1000)
        if res > 0:
            raw = self.publisher.recv()
            query = fedmsg.encoding.loads(raw.decode('utf-8'))
            try:
                self.publisher.send_multipart([
                    fedmsg.encoding.dumps(m).encode('utf-8')
                    for m in self.store.get(query)
                ])
            except ValueError as e:
                self.publisher.send(
                    u"error: '{0}'".format(six.text_type(e)).encode('utf-8'))

    def listen(self):
        try:
            while True:
                self._req_rep_cycle()
        finally:
            self.publisher.close()


def get_replay(name, query, config, context=None):
    """
    Query the replay endpoint for missed messages.

    Args:
        name (str): The replay endpoint name.
        query (dict): A dictionary used to query the replay endpoint for messages.
            Queries are dictionaries with the following any of the following keys:

            * 'seq_ids': A ``list`` of ``int``, matching the seq_id attributes
              of the messages. It should return at most as many messages as the
              length of the list, assuming no duplicate.

            * 'seq_id': A single ``int`` matching the seq_id attribute of the message.
              Should return a single message. It is intended as a shorthand for
              singleton ``seq_ids`` queries.

            * 'seq_id_range': A two-tuple of ``int`` defining a range of seq_id to check.

            * 'msg_ids': A ``list`` of UUIDs matching the msg_id attribute of the messages.

            * 'msg_id': A single UUID for the msg_id attribute.

            * 'time': A tuple of two timestamps. It will return all messages emitted in between.
        config (dict): A configuration dictionary. This dictionary should contain, at a
            minimum, two keys. The first key, 'replay_endpoints', should be a dictionary
            that maps ``name`` to a ZeroMQ socket. The second key, 'io_threads', is an
            integer used to initialize the ZeroMQ context.
        context (zmq.Context): The ZeroMQ context to use. If a context is not provided,
            one will be created.

    Returns:
        generator: A generator that yields message dictionaries.
    """
    endpoint = config.get('replay_endpoints', {}).get(name, None)
    if not endpoint:
        raise IOError("No appropriate replay endpoint "
                      "found for {0}".format(name))

    if not context:
        context = zmq.Context(config['io_threads'])

    # A replay endpoint isn't PUB/SUB but REQ/REP, as it allows
    # for bidirectional communication
    socket = context.socket(zmq.REQ)
    try:
        socket.connect(endpoint)
    except zmq.ZMQError as e:
        raise IOError("Error when connecting to the "
                      "replay endpoint: '{0}'".format(str(e)))

    # REQ/REP dance
    socket.send(fedmsg.encoding.dumps(query).encode('utf-8'))
    msgs = socket.recv_multipart()
    socket.close()

    for m in msgs:
        try:
            yield fedmsg.encoding.loads(m.decode('utf-8'))
        except ValueError:
            # We assume that if it isn't JSON then it's an error message
            raise ValueError(m)


def check_for_replay(name, names_to_seq_id, msg, config, context=None):
    """
    Check to see if messages need to be replayed.

    Args:
        name (str): The consumer's name.
        names_to_seq_id (dict): A dictionary that maps names to the last seen sequence ID.
        msg (dict): The latest message that has arrived.
        config (dict): A configuration dictionary. This dictionary should contain, at a
            minimum, two keys. The first key, 'replay_endpoints', should be a dictionary
            that maps ``name`` to a ZeroMQ socket. The second key, 'io_threads', is an
            integer used to initialize the ZeroMQ context.
        context (zmq.Context): The ZeroMQ context to use. If a context is not provided,
            one will be created.

    Returns:
        list: A list of message dictionaries.
    """
    prev_seq_id = names_to_seq_id.get(name, None)
    cur_seq_id = msg.get("seq_id", None)

    if prev_seq_id is None or cur_seq_id is None:
        return [msg]

    if cur_seq_id <= prev_seq_id:
        # Might have been delayed by network lag or something, in which case
        # we assume the replay has already been asked for and we dismiss it
        return []

    if cur_seq_id == prev_seq_id + 1 or prev_seq_id < 0:
        ret = [msg]
    else:
        ret = list(get_replay(name, {
            "seq_id_range": (prev_seq_id, cur_seq_id)
        }, config, context))

        if len(ret) == 0 or ret[-1]['seq_id'] < msg['seq_id']:
            ret.append(msg)

    names_to_seq_id[name] = cur_seq_id

    return ret
