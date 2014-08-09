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

import six
import zmq
import logging
import inspect
import subprocess

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


def set_high_water_mark(socket, config):
    """ Set a high water mark on the zmq socket.  Do so in a way that is
    cross-compatible with zeromq2 and zeromq3.
    """

    if config['high_water_mark']:
        if hasattr(zmq, 'HWM'):
            # zeromq2
            socket.setsockopt(zmq.HWM, config['high_water_mark'])
        else:
            # zeromq3
            socket.setsockopt(zmq.SNDHWM, config['high_water_mark'])
            socket.setsockopt(zmq.RCVHWM, config['high_water_mark'])


# TODO -- this should be in kitchen, not fedmsg
def guess_calling_module(default=None):
    # Iterate up the call-stack and return the first new top-level module
    for frame in (f[0] for f in inspect.stack()):
        modname = frame.f_globals['__name__'].split('.')[0]
        if modname != "fedmsg":
            return modname

    # Otherwise, give up and just return the default.
    return default


def set_tcp_keepalive(socket, config):
    """ Set a series of TCP keepalive options on the socket if
    and only if
      1) they are specified explicitly in the config and
      2) the version of pyzmq has been compiled with support

    We ran into a problem in FedoraInfrastructure where long-standing
    connections between some hosts would suddenly drop off the
    map silently.  Because PUB/SUB sockets don't communicate
    regularly, nothing in the TCP stack would automatically try and
    fix the connection.  With TCP_KEEPALIVE options (introduced in
    libzmq 3.2 and pyzmq 2.2.0.1) hopefully that will be fixed.

    See the following
      - http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/overview.html
      - http://api.zeromq.org/3-2:zmq-setsockopt
    """

    keepalive_options = {
        # Map fedmsg config keys to zeromq socket constants
        'zmq_tcp_keepalive': 'TCP_KEEPALIVE',
        'zmq_tcp_keepalive_cnt': 'TCP_KEEPALIVE_CNT',
        'zmq_tcp_keepalive_idle': 'TCP_KEEPALIVE_IDLE',
        'zmq_tcp_keepalive_intvl': 'TCP_KEEPALIVE_INTVL',
    }
    for key, const in keepalive_options.items():
        if key in config:
            attr = getattr(zmq, const, None)
            if attr:
                socket.setsockopt(attr, config[key])


def set_tcp_reconnect(socket, config):
    """ Set a series of TCP reconnect options on the socket if
    and only if
      1) they are specified explicitly in the config and
      2) the version of pyzmq has been compiled with support

    Once our fedmsg bus grew to include many hundreds of endpoints, we started
    notices a *lot* of SYN-ACKs in the logs.  By default, if an endpoint is
    unavailable, zeromq will attempt to reconnect every 100ms until it gets a
    connection.  With this code, you can reconfigure that to back off
    exponentially to some max delay (like 1000ms) to reduce reconnect storm
    spam.

    See the following
      - http://api.zeromq.org/3-2:zmq-setsockopt
    """

    reconnect_options = {
        # Map fedmsg config keys to zeromq socket constants
        'zmq_reconnect_ivl': 'RECONNECT_IVL',
        'zmq_reconnect_ivl_max': 'RECONNECT_IVL_MAX',
    }
    for key, const in reconnect_options.items():
        if key in config:
            attr = getattr(zmq, const, None)
            if attr:
                socket.setsockopt(attr, config[key])


def load_class(location):
    """ Take a string of the form 'fedmsg.consumers.ircbot:IRCBotConsumer'
    and return the IRCBotConsumer class.
    """
    mod_name, cls_name = location = location.strip().split(':')
    tokens = mod_name.split('.')

    fromlist = '[]'
    if len(tokens) > 1:
        fromlist = '.'.join(tokens[:-1])

    module = __import__(mod_name, fromlist=fromlist)

    try:
        return getattr(module, cls_name)
    except AttributeError as e:
        raise ImportError("%r not found in %r" % (cls_name, mod_name))


def dict_query(dic, query):
    """ Query a dict with 'dotted notation'.  Returns an OrderedDict.

    A query of "foo.bar.baz" would retrieve 'wat' from this::

        dic = {
            'foo': {
                'bar': {
                    'baz': 'wat',
                }
            }
        }

    Multiple queries can be specified if comma-separated.  For instance, the
    query "foo.bar.baz,foo.bar.something_else" would return this::

        OrderedDict({
            "foo.bar.baz": "wat",
            "foo.bar.something_else": None,
        })

    """

    if not isinstance(query, six.string_types):
        raise ValueError("query must be a string, not %r" % type(query))

    def _browse(tokens, d):
        """ Recurse through a dict to retrieve a value. """
        current, rest = tokens[0], tokens[1:]

        if not rest:
            return d.get(current, None)

        if current in d:
            if isinstance(d[current], dict):
                return _browse(rest, d[current])
            elif rest:
                return None
            else:
                return d[current]

    keys = [key.strip().split('.') for key in query.split(',')]
    return OrderedDict([
        ('.'.join(tokens), _browse(tokens, dic)) for tokens in keys
    ])

def cowsay_output(message):
    """ Invoke a shell command to print cowsay output. Primary replacement for
    os.system calls.
    """
    command = 'cowsay "%s"' % message
    ret = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    output, error = ret.communicate()
    return output, error
