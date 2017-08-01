==========
Publishing
==========

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
