Python API:  Consuming Messages
===============================

The other side of the :doc:`publishing` document is consuming messages.

"Naive" Consuming
-----------------

The most straightforward way, programmatically, to consume messages is to use
:func:`fedmsg.tail_messages`.  It is a generator that yields 4-tuples of the
form ``(name, endpoint, topic, message)``::

    >>> import fedmsg
    >>> for name, endpoint, topic, message in fedmsg.tail_messages():
    ...     print name, endpoint, topic, message

The API is easy to use and should hopefully make your scripts easy to understand
and maintain.  The downside here is that :func:`fedmsg.tail_messages` is
spinning in a sleep, listen, yield loop that is quite costly in IO and CPU
terms.  Typically, a script that uses :func:`fedmsg.tail_messages` will
consume 100% of a CPU.

For production services, you will want to use the hub-consumer approach
described further below.

.. note:: The ``fedmsg-tail`` command described in :doc:`commands` uses
          :func:`fedmsg.tail_messages` to "tail" the bus.

"Naive" API
~~~~~~~~~~~
.. autofunction:: fedmsg.tail_messages

The Hub-Consumer Approach
-------------------------

In contrast to the "naive" approach above, a more efficient way of
consuming events can be accomplished by way of the fedmsg-hub.  The drawback is
that programming it is a sort of indirect and declarative; it can be
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

 * Register your class on the ``moksha.consumer`` python entry-point.

An Example From "busmon"
~~~~~~~~~~~~~~~~~~~~~~~~
In the `busmon <https://github.com/ralphbean/busmon>`_ app, all messages from
the hub are processed to be formatted and displayed on a client's browser.  We
mark them up with a pretty-print format and use pygments to colorize them.

In the example below, the ``MessageColorizer`` consumer simply subscribes
to '*'; it will receive every message that hits it's local fedmsg-hub.

The ``config_key = 'busmon.consumers.enabled'`` line means that a
``'busmon.consumers.enabled': True`` entry must appear in the
fedmsg config for the consumer to be enabled.

Here's the full example from `busmon <https://github.com/ralphbean/busmon>`_, it
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
