===================
Developer Interface
===================

This documentation covers the public interfaces fedmsg provides. Unless otherwise noted,
all documented interfaces follow `Semantic Versioning 2.0.0`_. If the interface you depend
on is not documented here, it may change without warning in a minor release.

.. _api-python:

Python
======

.. _api-send-receive:

Sending and Receiving Messages
------------------------------

.. automodule:: fedmsg
    :members: init, destroy, publish, tail_messages

.. autoclass:: fedmsg.consumers.FedmsgConsumer


.. _api-config:

Configuration
-------------

.. automodule:: fedmsg.config
    :members: load_config, build_parser, execfile


.. _api-crypto:

Cryptography and Message Signing
--------------------------------

.. automodule:: fedmsg.crypto
    :members:
    :undoc-members:
    :show-inheritance:

Message Encoding
----------------

.. automodule:: fedmsg.encoding
    :members:
    :undoc-members:
    :show-inheritance:

.. autofunction:: fedmsg.encoding.dumps

.. autofunction:: fedmsg.encoding.pretty_dumps

SQLAlchemy Encoding Utilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: fedmsg.encoding.sqla
    :members:
    :undoc-members:
    :show-inheritance:


"Natural Language" Representation of Messages
---------------------------------------------

.. automodule:: fedmsg.meta
    :members:
    :undoc-members:
    :show-inheritance:

.. autodata:: processors

.. automodule:: fedmsg.meta.base
    :members:
    :undoc-members:
    :show-inheritance:


Replay
------

.. automodule:: fedmsg.replay
    :members: check_for_replay, get_replay


The fedmsg Protocol
===================

fedmsg uses `ZeroMQ Publish-Subscribe`_ (PUBSUB) sockets for the messages sent by
:func:`fedmsg.publish` and the messages received by :func:`fedmsg.tail_messages`
or by way of the Moksha Hub-Consumer approach.

.. warning::
    The message format described below is *not* part of the public API at this time.

The published ZeroMQ message consists of a multi-part message of exactly two frames,
formatted on the wire as follows:

* Frame 0: The message topic against which subscribers will perform a binary comparison.

* Frame 1: The JSON-serialized, UTF-8 encoded message.


.. _ZeroMQ Publish-Subscribe: https://rfc.zeromq.org/spec:29/PUBSUB/
.. _semantic versioning 2.0.0: http://semver.org/
