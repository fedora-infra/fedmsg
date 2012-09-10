Python API:  Consuming Messages
-------------------------------

 * TODO - naive consumption
 * TODO - autodoc FedmsgConsumer
 * TODO - example of writing a client/desktop consumer

Consuming events is accomplished by way of the fedmsg-hub.  For example,
in the `busmon <https://github.com/ralphbean/busmon>`_ app, all messages from
the hub are processed to be formatted and displayed on a client's browser.  We
mark them up with a pretty-print format and use pygments to colorize them.

Here are the *important* parts:  you must define a new class which extends
``moksha.api.hub:Consumer``, declares a ``topic`` attribute, a ``config_key``
attribute, and a ``consume``  method.

The ``topic`` is used soley for constraining what messages make their way
to the consumer; the consumer can *send* messages on any topic.  You may use
'splats' ('*') in the topic and subscribe to ``'org.fedoraproject.stg.koji.*'``
to get all of the messages from koji in the staging environment.  In the example
below, the ``MessageColorizer`` consumer simply subscribes to '*'; it will
receive every message that hits it's local fedmsg-hub.

The ``config_key`` is used to determine whether or not to actually run the
consumer.  In the below example, ``config_key = 'busmon.consumers.enabled'``.
This means that a ``'busmon.consumers.enabled': True`` entry must appear in the
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
