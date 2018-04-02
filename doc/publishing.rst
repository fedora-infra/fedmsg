.. _publishing:

==========
Publishing
==========

.. _legacy-publishing:

Publishing without a Broker
===========================

.. warning:: The APIs described in this section have been deprecated and will be
    removed in a future release. You should use the APIs described in
    :ref:`publishing`.

Before you start publishing messages, it is recommended that you call
:func:`fedmsg.init`. This should be done from every Python thread you intend
to publish messages from, and should be done early in your application's
initialization. The reason for this is that this call creates a thread-local
:class:`zmq.Context` and bind to a socket for publishing.

.. warning:: Since the network's latency is not 0, it can take some time before
    a subscriber has set up its connection to the publishing socket. When a
    publishing socket has no subscribers, it simply drops the published message.
    Currently, the only way to avoid lost messages is to initialize the socket
    as early as you can.

To publish a message, call :func:`fedmsg.publish`. Your message should be a
Python dictionary capable of being JSON-serialized. Additionally, any strings
it contains should be a text type. That is, :class:`unicode` in Python 2 and
:class:`str` in Python 3.


Publishing Through a Relay
==========================

It's possible to avoid having each thread bind to a socket for publishing. To
do so, you need to set up a :ref:`command-relay` service. Once it's running, you
need to set :ref:`conf-active` to ``True``, which causes publishing sockets to
connect to the socket specified in :ref:`conf-relay-inbound`.


.. _publishing-sans-zmq:

Publishing Without ZeroMQ
=========================

fedmsg also supports publishing your messages via `STOMP
<https://stomp.github.io/>`_. Brokers that support STOMP include `RabbitMQ
<https://www.rabbitmq.com/>`_ and `Apache ActiveMQ <http://activemq.apache.org/>`_.
Consult the :ref:`conf-stomp` for details on how to configure this.


Common Problems
===============

There are a set of problems users commonly encounter when publishing messages,
nearly all of them related to configuration. Check the logs to see if there are
any helpful messages.


ZeroMQ Not Enabled
------------------

fedmsg supports publishing messages using protocols other than ZeroMQ. If you neglect
to set :ref:`conf-zmq-enabled` to ``True``, fedmsg will attempt to publish the message
with `Moksha's Hub <https://moksha.readthedocs.io/en/latest/main/MokshaHub/>`_. If the
hub has not been initialized, you'll receive an :class:`AttributeError` when you call
:func:`fedmsg.publish`.


No Endpoints Available
----------------------

Currently, unless you are publishing through a relay, you must declare a list
of endpoints that fedmsg can bind to. Each Python thread, when :func:`fedmsg.init`
is called, iterates through the list and attempts to bind to each address. If it
is unable to bind to any address, an :class:`IOError` is raised. The solution is
to add more endpoints to the configuration.


Publishing with the Broker
==========================

.. note:: This describes the new publishing API was added in fedmsg version 1.1.0.
    This API is still experimental and may change without a major release of fedmsg.
    However, all changes will be clearly noted in the change log. Please provide
    any feedback you have on this API! For documentation on the old approach,
    see :ref:`legacy-publishing`.

Before you can publish messages, you need to start the fedmsg broker service.

Fedmsg Broker
=============

The broker service binds a socket and clients submit messages to the service for
publication. By default, the service uses the inter-process communication transport
and is run on the same host as the clients, but it can also use TCP and run on a
different host.

The fedmsg broker can be started using the provided systemd unit files, or run
in the foreground using::

    $ fedmsg broker

To change the broker configuration, either provide the configuration values using
the command line interface's flags (use ``fedmsg broker --help`` for the list of
available flags) or set the :ref:`broker-config` options in fedmsg's
configuration files.


Sending a Message
=================

Once the fedmsg broker is running, you should be able to publish a message. However,
you should first set up a subscribing socket to actually _see_ the message::

    >>> import zmq
    >>> context = zmq.Context()
    >>> sock = context.socket(zmq.SUB)
    >>> sock.setsockopt(zmq.SUBSCRIBE, b'')
    >>> sock.connect('tcp://127.0.0.1:9940')
    >>> sock.recv_multipart()  # This will block until you go to the next step

Now send the message::

    >>> from fedmsg.api import publish
    >>> publish(topic=u'demo.success', body={u'Hello': u'World!'})

You'll see the broker announce it received your message and sent it, and you'll
see it pop up in the terminal you're listening on!
