Fedora Infrastructure Message Bus
=================================

We want to hook all the services in Fedora Infrastructure up to send messages to
one another over a message bus instead of communicating with each other in
the heterogenous, "Rube-Goldberg" ways they do now.

``fedmsg`` (Fedora-Messaging) is a python package and API used around
Fedora Infrastructure to send and receive messages to and from applications.
See :doc:`overview` for a thorough introduction.


`Click here to see a feed of the Fedora bus
<https://apps.fedoraproject.org/datagrepper/raw>`_.  There's also a
``#fedora-fedmsg`` channel on the freenode network with a firehose bot echoing
messages to channel to help give you a feel for what's going on.

Receiving Messages with Python
------------------------------

.. code-block:: python

    import fedmsg

    # Yield messages as they're available from a generator
    for name, endpoint, topic, msg in fedmsg.tail_messages():
        print topic, msg

Receiving Messages from the Shell
---------------------------------

.. code-block:: bash

    $ fedmsg-tail --really-pretty

Publishing Messages with Python
-------------------------------

See :doc:`development` on setting up your environment and workflow.

.. code-block:: python

   import fedmsg
   fedmsg.publish(topic='testing', modname='test', msg={
       'test': "Hello World",
   })

Publishing Messages from the Shell
----------------------------------

.. code-block:: bash

   $ echo "Hello World." | fedmsg-logger --modname=git --topic=repo.update
   $ echo '{"a": 1}' | fedmsg-logger --json-input
   $ fedmsg-logger --message="This is a message."
   $ fedmsg-logger --message='{"a": 1}' --json-input

Testimonials
------------

- `Jordan Sissel <http://www.semicomplete.com>`_ -- "Cool idea, gives new
  meaning to open infrastructure."
- `David Gay <http://oddshocks.com>`_ -- "It's like I'm working with software
  made by people who thought about the future."


Community
---------

The source for this document can be found `on github
<https://github.com/fedora-infra/fedmsg>`_.  The issue tracker can be `found
there <https://github.com/fedora-infra/fedmsg/issues>`_, too.

Almost all discussion happens in ``#fedora-apps`` on the freenode network.
There is also a `mailing list
<https://admin.fedoraproject.org/mailman/listinfo/messaging-sig>`_.

Table of Contents
-----------------

.. toctree::
   :maxdepth: 0

   overview
   topology
   status
   FAQ
   development
   deployment
   commands
   publishing
   consuming
   encoding
   crypto
   replay
   meta
   config
   topics

----

.. note::
   :doc:`proposal` is a now out-moded document, but is kept here for historical
   purposes.
