.. _conf:

=============
Configuration
=============

fedmsg requires some configuration before it will work properly.


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
``str`` - A list of special zeromq endpoints where the inbound,
passive zmq SUB sockets for for instances of ``fedmsg-relay`` are
listening.

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

    make_short=lambda url: requests.get('http://api.bitly.com/v3/shorten?login=YOURLOGIN&apiKey=YOURAPIKEY&longUrl=%s&format=txt' % url).text.strip()

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
