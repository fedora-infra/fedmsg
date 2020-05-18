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
"""
The configuration values used at runtime are determined by checking in
the following order:

    - Built-in defaults
    - All Python files in the /etc/fedmsg.d/ directory
    - All Python files in the ~/.fedmsg.d/ directory
    - All Python files in the current working directory's fedmsg.d/ directory
    - Command line arguments

Within each directory, files are loaded in lexicographical order.

For example, if a config value does not appear in either the config file or on
the command line, then the built-in default is used.  If a value appears in
both the config file and as a command line argument, then the command line
value is used.

You can print the runtime configuration to the terminal by using the
``fedmsg-config`` command implemented by
:func:`fedmsg.commands.config.config`.


General configuration
=====================

.. _conf-active:

active
------
A boolean that, if ``True``, will cause the publishing socket to connect to the
:ref:`conf-relay-inbound` socket, rather than binding its own socket.


.. _conf-topic-prefix:

topic_prefix
------------
A string prefixed to the topics of all outgoing messages.

The default value is ``org.fedoraproject``.


.. _conf-environment:

environment
-----------
A string that must be one of ``['prod', 'stg', 'dev']``.  It signifies
the environment in which this fedmsg process is running and can be used
to weakly separate different logical buses running in the same
infrastructure.  It is used by :func:`fedmsg.publish` when it is
constructing a fully-qualified topic.


.. _conf-status-directory:

status_directory
----------------
A string that is the absolute path to a directory where consumers can save the
status of their last processed message.  In conjunction with
`datagrepper_url`_, allows for automatic retrieval of backlog on daemon
startup.


.. _conf-datagrepper-url:

datagrepper_url
---------------
A URL to an instance of the `datagrepper
<https://github.com/fedora-infra/datagrepper>`_ web service, such as
https://apps.fedoraproject.org/datagrepper/raw.  Can be used in conjunction with
`status_directory`_ to allow for automatic retrieval of backlog on daemon
startup.


.. _conf-endpoints:

endpoints
---------
``dict`` - A mapping of "service keys" to "zeromq endpoints"; the
heart of fedmsg.

``endpoints`` is "a list of possible addresses from which fedmsg can
send messages."  Thus, "subscribing to the bus" means subscribing to
every address listed in this dictionary.

``endpoints`` is also an index where a fedmsg process can look up
what port it should bind to to begin emitting messages.

When :func:`fedmsg.init` is invoked, a "name" is determined.  It is
either passed explicitly, or guessed from the call stack.  The name is
combined with the hostname of the process and used as a lookup key in
the ``endpoints`` dict.

When sending, fedmsg will attempt to bind to each of the addresses
listed under its service key until it can succeed in acquiring the port.
There needs to be as many endpoints listed as there will be
``processes * threads`` trying to publish messages for a given
service key.

For example, the following config provides for four WSGI processes on
bodhi on the machine app01 to send fedmsg messages.

  >>> config = dict(
  ...     endpoints={
  ...         "bodhi.app01":  [
  ...               "tcp://app01.phx2.fedoraproject.org:3000",
  ...               "tcp://app01.phx2.fedoraproject.org:3001",
  ...               "tcp://app01.phx2.fedoraproject.org:3002",
  ...               "tcp://app01.phx2.fedoraproject.org:3003",
  ...         ],
  ...     },
  ... )

If apache is configured to start up five WSGI processes, the fifth
one will produce tracebacks complaining with
``IOError("Couldn't find an available endpoint.")``.

If apache is configured to start up four WSGI processes, but with two
threads each, four of those threads will raise exceptions with the same
complaints.

A process subscribing to the fedmsg bus will connect a zeromq SUB
socket to every endpoint listed in the ``endpoints`` dict.  Using
the above config, it would connect to the four ports on
app01.phx2.fedoraproject.org.

.. note::  This is possibly the most complicated and hardest to
   understand part of fedmsg.  It is the black sheep of the design.  All
   of the simplicity enjoyed by the python API is achieved at cost of
   offloading the complexity here.

   Some work could be done to clarify the language used for "name" and
   "service key".  It is not always consistent in :mod:`fedmsg.core`.


.. _conf-srv-endpoints:

srv_endpoints
-------------
``list`` - A list of domain names for which to query SRV records
to get the associated endpoints.

When using fedmsg.config.load_config(), the DNS lookup is done and the
resulting endpoints are added to config['endpoint'][$DOMAINNAME]

For example, the following would query the endpoints for foo.example.com.

  >>> config = dict(
  ...     srv_endpoints=[foo.example.com]
  ...)


.. _conf-replay-endpoints:

replay_endpoints
----------------
``dict`` - A mapping of service keys, the same as for `endpoints`_
to replay endpoints, each key having only one. The replay endpoints are
special ZMQ endpoints using a specific protocol to allow the client to
request a playback of messages in case some have been dropped, for
instance due to network failures.

If the service has a replay endpoint specified, fedmsg will automatically
try to detect such failures and properly query the endpoint to get the
playback if needed.


.. _conf-relay-inbound:

relay_inbound
-------------
``str`` - A special zeromq endpoint where the inbound, passive zmq SUB
sockets for instances of ``fedmsg-relay`` are listening.

Commands like ``fedmsg-logger`` actively connect here and publish their
messages.

See :doc:`commands` for more information.


.. _conf-relay-outbound:

relay_outbound
--------------
``str`` - A list of special zeromq endpoints where the outbound
sockets for instances of ``fedmsg-relay`` should bind.


.. _conf-fedmsg.consumers.gateway.port:

fedmsg.consumers.gateway.port
-----------------------------
``int`` - A port number for the special outbound zeromq PUB socket
posted by :func:`fedmsg.commands.gateway.gateway`.  The
``fedmsg-gateway`` command is described in more detail in
:doc:`commands`.


Authentication and Authorization
================================

The following settings relate to message authentication and authorization.


.. _conf-sign-messages:

sign_messages
-------------
``bool`` - If set to true, then :mod:`fedmsg.core` will try to sign
every message sent using the machinery from :mod:`fedmsg.crypto`.

It is often useful to set this to `False` when developing.  You may not
have X509 certs or the tools to generate them just laying around.  If
disabled, you will likely want to also disable
`validate_signatures`_.


.. _conf-validate-signatures:

validate_signatures
-------------------
``bool`` - If set to true, then the base class
:class:`fedmsg.consumers.FedmsgConsumer` will try to use
:func:`fedmsg.crypto.validate` to validate messages before handing
them off to the particular consumer for which the message is bound.

This is also used by :mod:`fedmsg.meta` to denote trustworthiness
in the natural language representations produced by that module.


.. _conf-crypto-backend:

crypto_backend
--------------
``str`` - The name of the :mod:`fedmsg.crypto` backend that should
be used to sign outgoing messages.  It may be either 'x509' or 'gpg'.


.. _conf-crypto-validate-backends:

crypto_validate_backends
------------------------
``list`` - A list of names of :mod:`fedmsg.crypto` backends that
may be used to validate incoming messages.


.. _conf-ssldir:

ssldir
------
``str`` - This should be directory on the filesystem
where the certificates used by :mod:`fedmsg.crypto` can be found.
Typically ``/etc/pki/fedmsg/``.


.. _conf-crl-location:

crl_location
------------
``str`` - This should be a URL where the certificate revocation list can
be found.  This is checked by :func:`fedmsg.crypto.validate` and
cached on disk.


.. _conf-crl-cache:

crl_cache
---------
``str`` - This should be the path to a filename on the filesystem where
the CRL downloaded from `crl_location`_ can be saved.  The python
process should have write access there.


.. _conf-crl-cache-expiry:

crl_cache_expiry
----------------
``int`` - Number of seconds to keep the CRL cached before checking
`crl_location`_ for a new one.


.. _conf-ca-cert-location:

ca_cert_location
----------------
``str`` - This should be a URL where the certificate authority cert can
be found.  This is checked by :func:`fedmsg.crypto.validate` and
cached on disk.


.. _conf-ca-cert-cache:

ca_cert_cache
-------------
``str`` - This should be the path to a filename on the filesystem where
the CA cert downloaded from `ca_cert_location`_ can be saved.  The
python process should have write access there.


.. _conf-ca-cert-cache-expiry:

ca_cert_cache_expiry
--------------------
``int`` - Number of seconds to keep the CA cert cached before checking
`ca_cert_location`_ for a new one.


.. _conf-certnames:

certnames
---------
``dict`` - This should be a mapping of certnames to cert prefixes.

The keys should be of the form ``<service>.<host>``.  For example:
``bodhi.app01``.

The values should be the prefixes of cert/key pairs to be found in
`ssldir`_.  For example, if
``bodhi-app01.stg.phx2.fedoraproject.org.crt`` and
``bodhi-app01.stg.phx2.fedoraproject.org.key`` are to be found in
`ssldir`_, then the value
``bodhi-app01.stg.phx2.fedoraproject.org`` should appear in the
`certnames`_ dict.

Putting it all together, this value could be specified as follows::

    certnames={
        "bodhi.app01": "bodhi-app01.stg.phx2.fedoraproject.org",
        # ... other certname mappings may follow here.
    }

.. note::

    This is one of the most cumbersome parts of fedmsg.  The reason we
    have to enumerate all these redundant mappings between
    "service.hostname" and "service-fqdn" has to do with the limitations
    of reverse dns lookup.  Case in point, try running the following on
    app01.stg inside Fedora Infrastructure's environment.

        >>> import socket
        >>> print socket.getfqdn()

    You might expect it to print "app01.stg.phx2.fedoraproject.org", but
    it doesn't.  It prints "memcached04.phx2.fedoraproject.org".  Since
    we can't rely on programatically extracting the fully qualified
    domain names of the host machine during runtime, we need to
    explicitly list all of the certs in the config.


.. _conf-routing-nitpicky:

routing_nitpicky
----------------
``bool`` - When set to True, messages whose topics do not appear in
`routing_policy`_ automatically fail the validation process
described in :mod:`fedmsg.crypto`.  It defaults to ``False``.


.. _conf-routing-policy:

routing_policy
--------------
A Python dictionary mapping fully-qualified topic names to lists of cert
names.  If a message's topic appears in the `routing_policy`_ and
the name on its certificate does not appear in the associated list, then
that message fails the validation process in :mod:`fedmsg.crypto`.

For example, a routing policy might look like this::

    routing_policy={
        "org.fedoraproject.prod.bodhi.buildroot_override.untag": [
            "bodhi-app01.phx2.fedoraproject.org",
            "bodhi-app02.phx2.fedoraproject.org",
            "bodhi-app03.phx2.fedoraproject.org",
            "bodhi-app04.phx2.fedoraproject.org",
        ],
    }

The above loosely translates to "messages about bodhi buildroot
overrides being untagged may only come from the first four app
servers."  If a message with that topic bears a cert signed by any
other name, then that message fails the validation process.

Expect that your :ref:`conf-routing-policy` (if you define one) will
become quite long.

The default is an empty dictionary.


ZeroMQ
======

The following settings are ZeroMQ configuration options.


.. _conf-high-water-mark:

high_water_mark
---------------
``int`` - An option to zeromq that specifies a hard limit on the maximum
number of outstanding messages to be queued in memory before reaching an
exceptional state.

For our pub/sub zeromq sockets, the exceptional state means *dropping
messages*.  See the upstream documentation for `ZMQ_HWM
<http://api.zeromq.org/2-1:zmq-setsockopt>`_ and `ZMQ_PUB
<http://api.zeromq.org/2-1:zmq-socket>`_.

A value of ``0`` means "no limit" and is the
recommended value for fedmsg.  It is referenced when initializing
sockets in :func:`fedmsg.init`.


.. _conf-io-threads:

io_threads
----------
``int`` - An option that specifies the size of a zeromq thread pool to
handle I/O operations.  See the upstream documentation for `zmq_init
<http://api.zeromq.org/2-1:zmq-init>`_.

This value is referenced when initializing the zeromq context in
:func:`fedmsg.init`.


.. _conf-post-init-sleep:

post_init_sleep
---------------
``float`` - A number of seconds to sleep after initializing and before
sending any messages.  Setting this to a value greater than zero is
required so that zeromq doesn't drop messages that we ask it to send
before the pub socket is finished initializing.

Experimentation needs to be done to determine and sufficiently small and
safe value for this number.  ``1`` is definitely safe, but annoyingly
large.


.. _conf-zmq-enabled:

zmq_enabled
-----------
``bool`` - A value that must be true.  It is present solely
for compatibility/interoperability with `moksha
<http://mokshaproject.net>`_.


.. _conf-zmq-reconnect-ivl:

zmq_reconnect_ivl
-----------------
``int`` - Number of miliseconds that zeromq will wait to reconnect
until it gets a connection if an endpoint is unavailable. This is in
miliseconds. See upstream `zmq options
<http://api.zeromq.org/3-2:zmq-setsockopt>`_ for more information.


.. _conf-zmq-reconnect-ivl-max:

zmq_reconnect_ivl_max
---------------------
``int`` - Max delay that you can reconfigure to reduce reconnect storm
spam.  This is in miliseconds. See upstream `zmq options
<http://api.zeromq.org/3-2:zmq-setsockopt>`_ for more information.


.. _conf-zmq-strict:

zmq_strict
----------
``bool`` - When false, allow splats ('*') in topic names when
subscribing.  When true, disallow splats and accept only strict matches
of topic names.

This is an argument to `moksha <http://mokshaproject.net>`_ and arose
there to help abstract away differences between the "topics" of zeromq
and the "routing_keys" of AMQP.


.. _conf-zmq-tcp-keepalive:

zmq_tcp_keepalive
-----------------
``int`` - Interpreted as a boolean.  If non-zero, then keepalive options
will be set.
See upstream `zmq options
<http://api.zeromq.org/3-2:zmq-setsockopt>`_ and general `overview
<http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/overview.html>`_.


.. _conf-zmq-tcp-keepalive-cnt:

zmq_tcp_keepalive_cnt
---------------------
``int`` - Number of keepalive packets to send before considering the
connection dead.
See upstream `zmq options
<http://api.zeromq.org/3-2:zmq-setsockopt>`_ and general `overview
<http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/overview.html>`_.


.. _conf-zmq-tcp-keepalive-idle:

zmq_tcp_keepalive_idle
----------------------
``int`` - Number of seconds to wait after last data packet before
sending the first keepalive packet.
See upstream `zmq options
<http://api.zeromq.org/3-2:zmq-setsockopt>`_ and general `overview
<http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/overview.html>`_.


.. _conf-zmq-tcp-keepalive-intvl:

zmq_tcp_keepalive_intvl
-----------------------

``int`` - Number of seconds to wait inbetween sending subsequent
keepalive packets.
See upstream `zmq options
<http://api.zeromq.org/3-2:zmq-setsockopt>`_ and general `overview
<http://tldp.org/HOWTO/TCP-Keepalive-HOWTO/overview.html>`_.


IRC
===


.. _conf-irc:

irc
---
``list`` - A list of ircbot configuration dicts.  This is the primary
way of configuring the ``fedmsg-irc`` bot implemented in
:func:`fedmsg.commands.ircbot.ircbot`.

Each dict contains a number of possible options.  Take the following
example:

  >>> config = dict(
  ...     irc=[
  ...         dict(
  ...             network='irc.freenode.net',
  ...             port=6667,
  ...             nickname='fedmsg-dev',
  ...             channel='fedora-fedmsg',
  ...             timeout=120,
  ...
  ...             make_pretty=True,
  ...             make_terse=True,
  ...             make_short=True,
  ...
  ...             filters=dict(
  ...                 topic=['koji'],
  ...                 body=['ralph'],
  ...             ),
  ...         ),
  ...     ],
  ... )

Here, one bot is configured.  It is to connect to the freenode network
on port 6667.  The bot's name will be ``fedmsg-dev`` and it will
join the ``#fedora-fedmsg`` channel.

``make_pretty`` specifies that colors should be used, if possible.

``make_terse`` specifies that the "natural language" representations
produced by :mod:`fedmsg.meta` should be echoed into the channel instead
of raw or dumb representations.

``make_short`` specifies that any url associated with the message
should be shortened with a link shortening service.  If `True`, the
https://da.gd/ service will be used.  You can alternatively specify a
`callable` to use your own custom url shortener, like this::

    >>> def make_short(url):
    ...     service_url = ('http://api.bitly.com/v3/shorten?login=YOURLOGIN&'
    ...                    'apiKey=YOURAPIKEY&longUrl={url}&format=txt')
    ...     return requests.get(service_url.format(url=url).text.strip()

The ``filters`` dict is not very smart.  In the above case, any message
that has 'koji' anywhere in the topic or 'ralph' anywhere in the JSON
body will be discarded and not echoed into ``#fedora-fedmsg``.  This is
an area that could use some improvement.


.. _conf-irc-color-lookup:

irc_color_lookup
----------------
A dictionary mapping module names to `MIRC irc color names
<https://www.mirc.com/colors.html>`_.  For example::

  >>> irc_color_lookup = {
  ...     "fas": "light blue",
  ...     "bodhi": "green",
  ...     "git": "red",
  ...     "tagger": "brown",
  ...     "wiki": "purple",
  ...     "logger": "orange",
  ...     "pkgdb": "teal",
  ...     "buildsys": "yellow",
  ...     "planet": "light green",
  ... }


.. _conf-irc-method:

irc_method
----------
the name of the method used to publish the messages on IRC.
Valid values are ``msg`` and ``notice``.

The default is ``notice``.


.. _conf-stomp:

STOMP Configuration
===================

When using STOMP, you need to set :ref:`conf-zmq-enabled` to ``False``.
Additionally, if you're using STOMP with TLS (recommended), you do not need
fedmsg's cryptographic signatures to validate messages so you can turn those
off by setting :ref:`conf-validate-signatures` to ``False``


.. _conf-stomp-uri:

stomp_uri
---------

A string of comma-separated brokers. For example::

    stomp_uri='broker01.example.com:61612,broker02.example.com:61612'

There is no default for this setting.

.. _conf-stomp-heartbeat:

stomp_heartbeat
---------------

The STOMP heartbeat interval, in milliseconds.

There is no default for this setting.


.. _conf-stomp-user:

stomp_user
----------

The username to use with STOMP when authenticating with the broker.

There is no default for this setting.


.. _conf-stomp-pass:

stomp_pass
----------

The password to use with STOMP when authenticating with the broker.

There is no default for this setting.


.. _conf-stomp-ssl-crt:

stomp_ssl_crt
-------------

The PEM-encoded x509 client certificate to use when authenticating with the broker.

There is no default for this setting.


.. _conf-stomp-ssl-key:

stomp_ssl_key
-------------

The PEM-encoded private key for the :ref:`conf-stomp-ssl-crt`.

There is no default for this setting.


.. _conf-stomp-queue:

stomp_queue
-----------

If set, this will cause the Moksha hub to only listen to the specified queue for all fedmsg
consumers. If it is not specified, the Moksha hub will listen to all topics declared by all
fedmsg consumers.

There is no default for this setting.
"""

import argparse
import copy
import logging
import os
import sys
import textwrap
import warnings

import six

from kitchen.iterutils import iterate
from fedmsg.encoding import pretty_dumps


_log = logging.getLogger(__name__)


bare_format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"


def _get_config_files():
    """
    Load the list of file paths for fedmsg configuration files.

    Returns:
        list: List of files containing fedmsg configuration.
    """
    config_paths = []
    if os.environ.get('FEDMSG_CONFIG'):
        config_location = os.environ['FEDMSG_CONFIG']
    else:
        config_location = '/etc/fedmsg.d'

    if os.path.isfile(config_location):
        config_paths.append(config_location)
    elif os.path.isdir(config_location):
        # list dir and add valid files
        possible_config_files = [os.path.join(config_location, p)
                                 for p in os.listdir(config_location) if p.endswith('.py')]
        for p in possible_config_files:
            if os.path.isfile(p):
                config_paths.append(p)
    if not config_paths:
        _log.info('No configuration files found in %s', config_location)
    return config_paths


def _validate_non_negative_int(value):
    """
    Assert a value is a non-negative integer.

    Returns:
        int: A non-negative integer number.

    Raises:
        ValueError: if the value can't be cast to an integer or is less than 0.
    """
    value = int(value)
    if value < 0:
        raise ValueError('Integer must be greater than or equal to zero')
    return value


def _validate_non_negative_float(value):
    """
    Assert a value is a non-negative float.

    Returns:
        float: A non-negative floating point number.

    Raises:
        ValueError: if the value can't be cast to an float or is less than 0.
    """
    value = float(value)
    if value < 0:
        raise ValueError('Floating point number must be greater than or equal to zero')
    return value


def _validate_none_or_type(t):
    """
    Create a validator that checks if a setting is either None or a given type.

    Args:
        t: The type to assert.

    Returns:
        callable: A callable that will validate a setting for that type.
    """
    def _validate(setting):
        """
        Check the setting to make sure it's the right type.

        Args:
            setting (object): The setting to check.

        Returns:
            object: The unmodified object if it's the proper type.

        Raises:
            ValueError: If the setting is the wrong type.
        """
        if setting is not None and not isinstance(setting, t):
            raise ValueError('"{}" is not "{}"'.format(setting, t))
        return setting
    return _validate


def _validate_bool(value):
    """
    Validate a setting is a bool.

    Returns:
        bool: The value as a boolean.

    Raises:
        ValueError: If the value can't be parsed as a bool string or isn't already bool.
    """
    if isinstance(value, six.text_type):
        if value.strip().lower() == 'true':
            value = True
        elif value.strip().lower() == 'false':
            value = False
        else:
            raise ValueError('"{}" must be a boolean ("True" or "False")'.format(value))

    if not isinstance(value, bool):
        raise ValueError('"{}" is not a boolean value.'.format(value))

    return value


class FedmsgConfig(dict):
    """
    The fedmsg configuration dictionary.

    To access the actual configuration, use the :data:`conf` instance of this
    class.
    """
    _loaded = False
    _defaults = {
        'topic_prefix': {
            'default': u'com.example',
            'validator': _validate_none_or_type(six.text_type),
        },
        'environment': {
            'default': u'dev',
            'validator': _validate_none_or_type(six.text_type),
        },
        'io_threads': {
            'default': 1,
            'validator': _validate_non_negative_int,
        },
        'post_init_sleep': {
            'default': 0.5,
            'validator': _validate_non_negative_float,
        },
        'timeout': {
            'default': 2,
            'validator': _validate_non_negative_int,
        },
        'print_config': {
            'default': False,
            'validator': _validate_bool,
        },
        'high_water_mark': {
            'default': 0,
            'validator': _validate_non_negative_int,
        },
        # milliseconds
        'zmq_linger': {
            'default': 1000,
            'validator': _validate_non_negative_int,
        },
        'zmq_enabled': {
            'default': True,
            'validator': _validate_bool,
        },
        'zmq_strict': {
            'default': False,
            'validator': _validate_bool,
        },
        'zmq_tcp_keepalive': {
            'default': 1,
            'validator': _validate_non_negative_int,
        },
        'zmq_tcp_keepalive_cnt': {
            'default': 3,
            'validator': _validate_non_negative_int,
        },
        'zmq_tcp_keepalive_idle': {
            'default': 60,
            'validator': _validate_non_negative_int,
        },
        'zmq_tcp_keepalive_intvl': {
            'default': 5,
            'validator': _validate_non_negative_int,
        },
        'zmq_reconnect_ivl': {
            'default': 100,
            'validator': _validate_non_negative_int,
        },
        'zmq_reconnect_ivl_max': {
            'default': 1000,
            'validator': _validate_non_negative_int,
        },
        'endpoints': {
            'default': {
                'relay_outbound': [
                    'tcp://127.0.0.1:4001',
                ]
            },
            'validator': None,
        },
        'relay_inbound': {
            'default': u'tcp://127.0.0.1:2001',
            'validator': _validate_none_or_type(six.text_type),
        },
        'fedmsg.consumers.gateway.port': {
            'default': 9940,
            'validator': _validate_non_negative_int,
        },
        'fedmsg.consumers.gateway.high_water_mark': {
            'default': 1000,
            'validator': _validate_non_negative_int,
        },
        'sign_messages': {
            'default': False,
            'validator': _validate_bool,
        },
        'validate_signatures': {
            'default': True,
            'validator': _validate_bool,
        },
        'crypto_backend': {
            'default': u'x509',
            'validator': _validate_none_or_type(six.text_type),
        },
        'crypto_validate_backends': {
            'default': ['x509'],
            'validator': _validate_none_or_type(list),
        },
        'ssldir': {
            'default': u'/etc/pki/fedmsg',
            'validator': _validate_none_or_type(six.text_type),
        },
        'crl_location': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'crl_cache': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'crl_cache_expiry': {
            'default': 3600,
            'validator': _validate_non_negative_int,
        },
        'ca_cert_location': {
            'default': u'/etc/pki/fedmsg/ca.crt',
            'validator': _validate_none_or_type(six.text_type),
        },
        'ca_cert_cache': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'ca_cert_cache_expiry': {
            'default': 0,
            'validator': _validate_non_negative_int,
        },
        'certnames': {
            'default': {},
            'validator': _validate_none_or_type(dict),
        },
        'routing_policy': {
            'default': {},
            'validator': _validate_none_or_type(dict),
        },
        'routing_nitpicky': {
            'default': False,
            'validator': _validate_bool,
        },
        'irc': {
            'default': [
                {
                    'network': 'irc.freenode.net',
                    'port': 6667,
                    'ssl': False,
                    'nickname': 'fedmsg-dev',
                    'channel': 'my-fedmsg-channel',
                    'timeout': 120,
                    'make_pretty': True,
                    'make_terse': True,
                    'make_short': True,
                    'line_rate': 0.9,
                    'filters': {
                        'topic': [],
                        'body': ['lub-dub'],
                    },
                },
            ],
            'validator': _validate_none_or_type(list),
        },
        'irc_color_lookup': {
            'default': {
                'fas': 'light blue',
                'bodhi': 'green',
                'git': 'red',
                'tagger': 'brown',
                'wiki': 'purple',
                'logger': 'orange',
                'pkgdb': 'teal',
                'buildsys': 'yellow',
                'planet': 'light green',
            },
            'validator': _validate_none_or_type(dict),
        },
        'irc_default_color': {
            'default': u'light grey',
            'validator': _validate_none_or_type(six.text_type),
        },
        'irc_method': {
            'default': u'notice',
            'validator': _validate_none_or_type(six.text_type),
        },
        'active': {
            'default': False,
            'validator': _validate_bool,
        },
        'persistent_store': {
            'default': None,
            'validator': None,
        },
        'logging': {
            'default': {
                'version': 1,
                'formatters': {
                    'bare': {
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                        "format": bare_format
                    },
                },
                'handlers': {
                    'console': {
                        "class": "logging.StreamHandler",
                        "formatter": "bare",
                        "level": "INFO",
                        "stream": "ext://sys.stdout",
                    }
                },
                'loggers': {
                    'fedmsg': {
                        "level": "INFO",
                        "propagate": False,
                        "handlers": ["console"],
                    },
                    'moksha': {
                        "level": "INFO",
                        "propagate": False,
                        "handlers": ["console"],
                    },
                },
            },
            'validator': _validate_none_or_type(dict),
        },
        'stomp_uri': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_user': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_pass': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_ssl_crt': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_ssl_key': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'datagrepper_url': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
    }

    def __getitem__(self, *args, **kw):
        """Load the configuration if necessary and forward the call to the parent."""
        if not self._loaded:
            self.load_config()
        return super(FedmsgConfig, self).__getitem__(*args, **kw)

    def get(self, *args, **kw):
        """Load the configuration if necessary and forward the call to the parent."""
        if not self._loaded:
            self.load_config()
        return super(FedmsgConfig, self).get(*args, **kw)

    def copy(self, *args, **kw):
        """Load the configuration if necessary and forward the call to the parent."""
        if not self._loaded:
            self.load_config()
        return super(FedmsgConfig, self).copy(*args, **kw)

    def load_config(self, settings=None):
        """
        Load the configuration either from the config file, or from the given settings.

        Args:
            settings (dict): If given, the settings are pulled from this dictionary. Otherwise, the
                config file is used.
        """
        self._load_defaults()
        if settings:
            self.update(settings)
        else:
            config_paths = _get_config_files()
            for p in config_paths:
                conf = _process_config_file([p])
                self.update(conf)
        self._loaded = True
        self._validate()

    def _load_defaults(self):
        """Iterate over self._defaults and set all default values on self."""
        for k, v in self._defaults.items():
            self[k] = v['default']

    def _validate(self):
        """
        Run the validators found in self._defaults on all the corresponding values.

        Raises:
            ValueError: If the configuration contains an invalid configuration value.
        """
        errors = []
        for k in self._defaults.keys():
            try:
                validator = self._defaults[k]['validator']
                if validator is not None:
                    self[k] = validator(self[k])
            except ValueError as e:
                errors.append('\t{}: {}'.format(k, six.text_type(e)))

        if errors:
            raise ValueError(
                'Invalid configuration values were set: \n{}'.format('\n'.join(errors)))


#: The fedmsg configuration dictionary. All valid configuration keys are
#: guaranteed to be in the dictionary and to have a valid value. This dictionary
#: should not be mutated. This is meant to replace the old :func:`load_config`
#: API, but is not backwards-compatible with it.
conf = FedmsgConfig()


defaults = dict(
    topic_prefix="org.fedoraproject",
    environment="dev",
    io_threads=1,
    post_init_sleep=0.5,
    timeout=2,
    print_config=False,
    high_water_mark=0,  # zero means no limit
    zmq_linger=1000,    # Wait one second before timing out on fedmsg-relay
    active=False,       # if active, "connect", else "bind"
                        # Generally active is true only for fedmsg-logger
    persistent_store=None,  # an object.  See the fedmsg.replay module.
    logging=dict(
        version=1,
        formatters=dict(
            bare={
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": bare_format
            },
        ),
        handlers=dict(
            console={
                "class": "logging.StreamHandler",
                "formatter": "bare",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            }
        ),
        loggers=dict(
            fedmsg={
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
            moksha={
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
        ),
    ),
)

__cache = {}


def load_config(extra_args=None,
                doc=None,
                filenames=None,
                invalidate_cache=False,
                fedmsg_command=False,
                disable_defaults=False):
    """ Setup a runtime config dict by integrating the following sources
    (ordered by precedence):

      - defaults (unless disable_defaults = True)
      - config file
      - command line arguments

    If the ``fedmsg_command`` argument is False, no command line arguments are
    checked.

    """
    warnings.warn('Using "load_config" is deprecated and will be removed in a future release;'
                  ' use the "fedmsg.config.conf" dictionary instead.', DeprecationWarning)
    global __cache

    if invalidate_cache:
        __cache = {}

    if __cache:
        return __cache

    # Coerce defaults if arguments are not supplied.
    extra_args = extra_args or []
    doc = doc or ""

    if not disable_defaults:
        config = copy.deepcopy(defaults)
    else:
        config = {}

    config.update(_process_config_file(filenames=filenames))

    # This is optional (and defaults to false) so that only 'fedmsg-*' commands
    # are required to provide these arguments.
    # For instance, the moksha-hub command takes a '-v' argument and internally
    # makes calls to fedmsg.  We don't want to impose all of fedmsg's CLI
    # option constraints on programs that use fedmsg, so we make it optional.
    if fedmsg_command:
        config.update(_process_arguments(extra_args, doc, config))

    # If the user specified a config file on the command line, then start over
    # but read in that file instead.
    if not filenames and config.get('config_filename', None):
        return load_config(extra_args, doc,
                           filenames=[config['config_filename']],
                           fedmsg_command=fedmsg_command,
                           disable_defaults=disable_defaults)

    # Just a little debug option.  :)
    if config.get('print_config'):
        print(pretty_dumps(config))
        sys.exit(0)

    if not disable_defaults and 'endpoints' not in config:
        raise ValueError("No config value 'endpoints' found.")

    if not isinstance(config.get('endpoints', {}), dict):
        raise ValueError("The 'endpoints' config value must be a dict.")

    if 'endpoints' in config:
        config['endpoints'] = dict([
            (k, list(iterate(v))) for k, v in config['endpoints'].items()
        ])

    if 'srv_endpoints' in config and len(config['srv_endpoints']) > 0:
        from dns.resolver import query, NXDOMAIN, Timeout, NoNameservers
        for e in config['srv_endpoints']:
            urls = []
            try:
                records = query('_fedmsg._tcp.{0}'.format(e), 'SRV')
            except NXDOMAIN:
                warnings.warn("There is no appropriate SRV records " +
                              "for {0}".format(e))
                continue
            except Timeout:
                warnings.warn("The DNS query for the SRV records of" +
                              " {0} timed out.".format(e))
                continue
            except NoNameservers:
                warnings.warn("No name server is available, please " +
                              "check the configuration")
                break

            for rec in records:
                urls.append('tcp://{hostname}:{port}'.format(
                    hostname=rec.target.to_text(),
                    port=rec.port
                ))
            config['endpoints'][e] = list(iterate(urls))

    if 'topic_prefix_re' not in config and 'topic_prefix' in config:
        # Turn "org.fedoraproject" into "org\.fedoraproject\.[^\W\d_]+"
        config['topic_prefix_re'] = config['topic_prefix'].replace('.', r'\.')\
            + r'\.[^\W\d_]+'

    __cache = config
    return config


def build_parser(declared_args, doc, config=None, prog=None):
    """ Return the global :class:`argparse.ArgumentParser` used by all fedmsg
    commands.

    Extra arguments can be supplied with the `declared_args` argument.
    """

    config = config or copy.deepcopy(defaults)
    prog = prog or sys.argv[0]

    parser = argparse.ArgumentParser(
        description=textwrap.dedent(doc),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=prog,
    )

    parser.add_argument(
        '--io-threads',
        dest='io_threads',
        type=int,
        help="Number of io threads for 0mq to use",
        default=config['io_threads'],
    )
    parser.add_argument(
        '--topic-prefix',
        dest='topic_prefix',
        type=str,
        help="Prefix for the topic of each message sent.",
        default=config['topic_prefix'],
    )
    parser.add_argument(
        '--post-init-sleep',
        dest='post_init_sleep',
        type=float,
        help="Number of seconds to sleep after initializing.",
        default=config['post_init_sleep'],
    )
    parser.add_argument(
        '--config-filename',
        dest='config_filename',
        help="Config file to use.",
        default=None,
    )
    parser.add_argument(
        '--print-config',
        dest='print_config',
        help='Simply print out the configuration and exit.  No action taken.',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--timeout',
        dest='timeout',
        help="Timeout in seconds for any blocking zmq operations.",
        type=float,
        default=config['timeout'],
    )
    parser.add_argument(
        '--high-water-mark',
        dest='high_water_mark',
        help="Limit on the number of messages in the queue before blocking.",
        type=int,
        default=config['high_water_mark'],
    )
    parser.add_argument(
        '--linger',
        dest='zmq_linger',
        help="Number of milliseconds to wait before timing out connections.",
        type=int,
        default=config['zmq_linger'],
    )

    for args, kwargs in declared_args:
        # Replace the hard-coded extra_args default with the config file value
        # (if it exists)
        if all([k in kwargs for k in ['dest', 'default']]):
            kwargs['default'] = config.get(
                kwargs['dest'], kwargs['default'])

        # Having slurped smart defaults from the config file, add the CLI arg.
        parser.add_argument(*args, **kwargs)

    return parser


def _process_arguments(declared_args, doc, config):
    parser = build_parser(declared_args, doc, config)
    args = parser.parse_args()
    return dict(args._get_kwargs())


def _gather_configs_in(directory):
    """ Return list of fully qualified python filenames in the given dir """
    try:
        return sorted([
            os.path.join(directory, fname)
            for fname in os.listdir(directory)
            if fname.endswith('.py')
        ])
    except OSError:
        return []


def _recursive_update(d1, d2):
    """ Little helper function that does what d1.update(d2) does,
    but works nice and recursively with dicts of dicts of dicts.

    It's not necessarily very efficient.
    """

    for k in set(d1).intersection(d2):
        if isinstance(d1[k], dict) and isinstance(d2[k], dict):
            d1[k] = _recursive_update(d1[k], d2[k])
        else:
            d1[k] = d2[k]

    for k in set(d2).difference(d1):
        d1[k] = d2[k]

    return d1


def execfile(fname, variables):
    """ This is builtin in python2, but we have to roll our own on py3. """
    with open(fname) as f:
        code = compile(f.read(), fname, 'exec')
        exec(code, variables)


def _process_config_file(filenames=None):

    filenames = filenames or []

    # Validate that these files are really files
    for fname in filenames:
        if not os.path.isfile(fname):
            raise ValueError("%r is not a file." % fname)

    # If nothing specified, look in the default locations
    if not filenames:
        filenames = [
            '/etc/fedmsg-config.py',
            os.path.expanduser('~/.fedmsg-config.py'),
            os.getcwd() + '/fedmsg-config.py',
        ]
        folders = ["/etc/fedmsg.d/", os.path.expanduser('~/.fedmsg.d/'),
                   os.getcwd() + '/fedmsg.d/', ]
        if 'VIRTUAL_ENV' in os.environ:
            folders.append(os.path.join(
                os.environ['VIRTUAL_ENV'], 'etc/fedmsg.d'))

        filenames = sum(map(_gather_configs_in, folders), []) + filenames

    # Each .ini file should really be a python module that
    # builds a config dict.
    config = {}
    for fname in filenames:
        if os.path.isfile(fname):
            variables = {}
            try:
                execfile(fname, variables)
                config = _recursive_update(config, variables['config'])
            except IOError as e:
                warnings.warn(str(e))

    return config
