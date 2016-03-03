Python API:  Consuming Messages
===============================

The other side of the :doc:`publishing` document is consuming messages.

.. note:: Messages that you consume come with a topic and a body (dict).  The content
   of a message can be useful!  For instance, messages from FAS that come when a
   user edits their profile can tell you who made the change and what fields
   were changed.  fedmsg was designed with security and message validation in
   mind, but its still so new that you shouldn't trust it.  When building
   consumers, you should *always* verify information with existing webapps
   before acting on messages.

   - **nirik>** trust, but verify. or... don't trust, and verify. ;)

.. note::
   This document is on *how* to consume messages.  But if you want to know
   *what* messages there are, you might check out :doc:`topics`.

"Naive" Consuming
-----------------

The most straightforward way, programmatically, to consume messages is to use
:func:`fedmsg.tail_messages`.  It is a generator that yields 4-tuples of the
form ``(name, endpoint, topic, message)``::

    >>> import fedmsg
    >>> import fedmsg.config

    >>> # Read in the config from /etc/fedmsg.d/
    >>> config = fedmsg.config.load_config()

    >>> for name, endpoint, topic, msg in fedmsg.tail_messages(mute=True, **config):
    ...     print topic, msg  # or use fedmsg.encoding.pretty_dumps(msg)

The API is easy to use and should hopefully make your scripts easy to understand
and maintain.

For production services, you will want to use the hub-consumer approach
described further below.

.. note:: If you installed fedmsg from PyPI (or source), make sure that
   you've installed the 'consumers' extra, which may be done like so:
   ``pip install fedmsg[consumers]``.

Note that the :func:`fedmsg.tail_messages` used to be quite inefficient;
it spun in a sleep, listen, yield loop that was quite costly in IO and CPU
terms.  Typically, a script that used :func:`fedmsg.tail_messages` would
consume 100% of a CPU.  That has since be resolved by introducing the use
of a ``zmq.Poller``.

.. note:: The ``fedmsg-tail`` command described in :doc:`commands` uses
          :func:`fedmsg.tail_messages` to "tail" the bus.

"Naive" API
~~~~~~~~~~~
.. autofunction:: fedmsg.tail_messages

The Hub-Consumer Approach
-------------------------

In contrast to the "naive" approach above, a more efficient way of
consuming events can be accomplished by way of the fedmsg-hub.  The drawback is
that programming it is sort of indirect and declarative; it can be
confusing at first.

To consume messages and do with them what you'd like, you need to:

 * Write a class which extends :class:`fedmsg.consumers.FedmsgConsumer`
 * Override certain properties and methods of that class.  Namely,

   * ``topic`` -- A string used soley for constraining what messages make
     their way to the consumer; the consumer can *send* messages on any
     topic.  You may use 'splats' ('*') in the topic and subscribe to
     ``'org.fedoraproject.stg.koji.*'`` to get all of the messages from
     koji in the staging environment.
   * ``config_key`` -- A string used to declare a configuration entry that must
     be set to ``True`` for your consumer to be activated by the fedmsg-hub.
   * ``consume`` -- A method that accepts a dict (the message) and contains code
     that "does what you would like to do".
   * ``replay_name`` -- (optional) The name of the replay endpoint where the system should
     query playback in case of missing messages. It must match a service key in
     :term:`replay_endpoints`.

 * Register your class on the ``moksha.consumer`` python entry-point.

A simple example
~~~~~~~~~~~~~~~~

`Luke Macken <http://lewk.org>`_ wrote a simple example of a `koji consumer
<https://github.com/lmacken/fedmsg-koji-consumer>`_.  It's a good place to
start if you're writing your own consumer.

An Example From "busmon"
~~~~~~~~~~~~~~~~~~~~~~~~
In the `busmon <https://github.com/fedora-infra/busmon>`_ app, all messages from
the hub are processed to be formatted and displayed on a client's browser.  We
mark them up with a pretty-print format and use pygments to colorize them.

In the example below, the ``MessageColorizer`` consumer simply subscribes
to '*'; it will receive every message that hits it's local fedmsg-hub.

The ``config_key = 'busmon.consumers.enabled'`` line means that a
``'busmon.consumers.enabled': True`` entry must appear in the
fedmsg config for the consumer to be enabled.

Here's the full example from `busmon <https://github.com/fedora-infra/busmon>`_, it
consumes messages from every topic, formats them in pretty colored HTML and then
re-sends them out on a new topic::

    import pygments.lexers
    import pygments.formatters

    import fedmsg
    import fedmsg.encoding
    import fedmsg.consumers

    class MessageColorizer(fedmsg.consumers.FedmsgConsumer):
        topic = "*"
        jsonify = False
        config_key = 'busmon.consumers.enabled'

        def consume(self, message):
            destination_topic = "colorized-messages"

            # Just so we don't create an infinite feedback loop.
            if self.destination_topic in message.topic:
                return

            # Format the incoming message
            code = pygments.highlight(
                fedmsg.encoding.pretty_dumps(fedmsg.encoding.loads(message.body)),
                pygments.lexers.JavascriptLexer(),
                pygments.formatters.HtmlFormatter(full=False)
            ).strip()

            # Ship it!
            fedmsg.publish(
                topic=self.destination_topic,
                msg=code,
            )

Now, just defining a consumer isn't enough to have it picked up by the ``fedmsg-hub`` when it runs.  You must also declare the consumer as an entry-point in your app's ``setup.py``, like this::

    setup(
        ...
        entry_points={
            'moksha.consumer': (
                'colorizer = busmon.consumers:MessageColorizer',
            ),
        },
    )

At initialization, ``fedmsg-hub`` looks for all the objects registered
on the ``moksha.consumer`` entry point and loads them

FedmsgConsumer API
~~~~~~~~~~~~~~~~~~
.. autoclass:: fedmsg.consumers.FedmsgConsumer


DIY - Listening with Raw zeromq
-------------------------------

So you want to receive messages without using any fedmsg libs? (say you're on
some ancient system where moksha and twisted won't fly) If you can get
python-zmq built, you're in good shape.  Use the following example script as a
starting point for whatever you want to build::

    #!/usr/bin/env python

    import json
    import pprint
    import zmq


    def listen_and_print():
        # You can listen to stg at "tcp://stg.fedoraproject.org:9940"
        endpoint = "tcp://hub.fedoraproject.org:9940"
        # Set this to something like org.fedoraproject.prod.compose
        topic = 'org.fedoraproject.prod.'

        ctx = zmq.Context()
        s = ctx.socket(zmq.SUB)
        s.connect(endpoint)

        s.setsockopt(zmq.SUBSCRIBE, topic)

        poller = zmq.Poller()
        poller.register(s, zmq.POLLIN)

        while True:
            evts = poller.poll()  # This blocks until a message arrives
            topic, msg = s.recv_multipart()
            print topic, pprint.pformat(json.loads(msg))

    if __name__ == "__main__":
        listen_and_print()

Just bear in mind that you don't reap any of the benefits of
:mod:`fedmsg.crypto` or :mod:`fedmsg.meta`.

.. note:: In the example above, the topic is just
   ``'org.fedoraproject.prod.'`` and *not* ``'org.fedoraproject.prod.*'``.
   The ``*`` that you see elsewhere is a Moksha convention and it is actually
   just stripped from the topic.

   Why? The ``*`` has meaning in AMQP, but not zeromq. The Moksha project
   (which underlies fedmsg) aims to be an abstraction layer over zeromq,
   AMQP, and STOMP and contains some code that allows use of the ``*`` for
   zeromq, in order to make it look more like AMQP or STOMP (superficially).
   fedmsg (being built on Moksha) inherits this behavior even though it
   only uses the zeromq backend.  See `these comments
   <http://threebean.org/blog/zeromq-and-fedmsg-diy/#disqus_thread>`_ for
   some discussion.
