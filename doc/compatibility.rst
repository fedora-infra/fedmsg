Compatibility with Other Messaging Technologies
===============================================

fedmsg was originally built to specifically support zeromq as its messaging backend.

However, we also originally built it on top of `moksha <http://moksha.ws>`_
which is a framework that already supports not only zeromq, but also STOMP and
AMQP. In 2016, we added the ability for fedmsg to send and receive messages
over those protocols (and any others that moksha ends up supporting).

This lets you take advantage of the litany of apps written around the fedmsg
ecosystem (FMN, fedmsg-irc, datanommer, fedimg, etc..) and run them in other
messaging environments (STOMP, AMQP, ...).

We intentionally support:

- *The hub/consumer approach*. If you have a fedmsg consumer, it should be able
  to listen to messages over other protocols now.
- *Publishing with fedmsg.publish*. This will only work from a fedmsg consumer.
  It will figure out the moksha context and ask it to publish on fedmsg's
  behalf, thereby publishing over STOMP or AMQP, depending on configuration.

We intentionally do not support:

- *The naive listening approach*, i.e. `fedmsg.tail_messages()`. It would be
  much more work and its not worth it in our opinion. If we find a really good
  reason to implement support for it, we can always revisit this later.

Configuration
-------------

In order to get a fedmsg-hub instance working with STOMP, you should add the
following configuration to `/etc/fedmsg.d/base.py`::

    # We almost always want the fedmsg-hub to be sending messages with zmq as
    # opposed to amqp or stomp.  You can send with only *one* of the messaging
    # backends: zeromq or amqp or stomp.  You cannot send with two or more at
    # the same time.  Here, zmq is either enabled, or it is not.  If it is not,
    # see the options below for how to configure stomp or amqp.
    #zmq_enabled=True,

    # On the other hand, if you wanted to use STOMP *instead* of zeromq, you
    # could do the following...
    zmq_enabled=False,
    stomp_uri='broker01.example.com:61612,broker02.example.com:61612',
    stomp_heartbeat=1000,
    stomp_user='username',
    stomp_pass='password',
    stomp_ssl_crt='/path/to/ssl.crt',
    stomp_ssl_key='/path/to/ssl.key',

    # This is optional.
    # If present, the hub will listen only to this queue for all fedmsg consumers.
    # If absent, the hub will listen to all topics declared by all fedmsg consumers.
    #stomp_queue='/queue/Consumer.yourqueue',

    # There's usually no point in cryptographically validating messages from
    # other busses.  They likely won't bear message certificates and signatures.
    # Other busses usually use TLS on the connection itself for authentication
    # and authorization.
    validate_signatures=False,
