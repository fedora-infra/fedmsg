===========
Subscribing
===========

There are two approaches to subscribing to messages that have been published.


The Generator Approach
======================

The first approach is to use the :func:`fedmsg.tail_messages` API. This returns
a generator that yields messages as they arrive::

    >>> import fedmsg
    >>> for name, endpoint, topic, msg in fedmsg.tail_messages():
    ...     print topic, msg

For this to print anything, you need to be :doc:`publishing` messages.

.. note:: This approach only works with messages published via ZeroMQ. If you
          are :ref:`publishing-sans-zmq` then you will need to use
          :ref:`consumer-approach`.


.. _consumer-approach:

The Consumer Approach
=====================

This approach requires a bit more work, but provides several advantages. Namely, it
manages workers for you and supports replaying missed messages via a network service.

The first step is to write a class which extends :class:`fedmsg.consumers.FedmsgConsumer`.
The class documentation covers the details of implementing a consumer.

After you have implemented your consumer class and registered it under the
``moksha.consumer`` Python entry-point, you need to start the :ref:`command-hub` service,
which will create your class in one or more worker threads and pass messages to these
workers as they arrive.

To see a working example of this pattern, investigate the :mod:`fedmsg.consumers.relay`
module.

Consuming Non-ZeroMQ Messages
-----------------------------

In order to consume messages with STOMP, you will need to set the :ref:`conf-stomp`
options.


Best Practices
==============

When using fedmsg, messages will be lost. Your applications and services should
be prepared to receive duplicate messages. Always provide a way for the application
or service to recover gracefully for a lost or duplicate message.
