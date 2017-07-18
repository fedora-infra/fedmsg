======
fedmsg
======

fedmsg (Federated Message Bus) is a library built on `ZeroMQ`_ using the `PyZMQ`_
Python bindings. fedmsg aims to make it easy to connect services together using
ZeroMQ publishers and subscribers.

Receiving messages in Python is as simple as:

.. code-block:: python

    import fedmsg

    # Yield messages as they're available from a generator
    for name, endpoint, topic, msg in fedmsg.tail_messages():
        print topic, msg

To publish a message:

.. code-block:: python

   import fedmsg
   fedmsg.publish(topic='testing', modname='test', msg={
       'test': "Hello World",
   })

.. note:: fedmsg requires some configuration before it can be used. See the
   :ref:`conf` documentation for more information.


User Guide
==========

.. toctree::
   :maxdepth: 2

   installation
   configuration
   commands
   publishing
   subscribing
   deployment
   changelog


API Guide
=========

.. toctree::
   :maxdepth: 3

   api


Contributor Guide
=================

.. toctree::
   :maxdepth: 2

   contributing


Community
=========

The source code and issue tracker are `on GitHub`_.


.. _On GitHub: https://github.com/fedora-infra/fedmsg/
.. _ZeroMQ: https://zeromq.org/
.. _PyZMQ: https://pyzmq.readthedocs.io/
