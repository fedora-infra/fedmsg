Federated Message Bus
=====================

Some time ago, the Fedora Infrastructure team wanted to hook all the services in
Fedora Infrastructure up to send messages to one another over a message bus instead
of communicating with each other in the heterogenous, "Rube-Goldberg" way they did
previously.

``fedmsg`` (FEDerated MeSsaGe bus) is a python package and API defining a brokerless
messaging architecture to send and receive messages to and from applications.
See :doc:`overview` for a thorough introduction.

While originally specific to Fedora, the expansion of the project's name was
changed away from the old "Fedora Messaging" to the current "Federated Message Bus"
after it was also adopted for
`use in Debian's infrastructure <https://wiki.debian.org/FedMsg>`_.

`Click here to see a feed of the Fedora bus
<https://apps.fedoraproject.org/datagrepper/raw>`_.  There's also a
``#fedora-fedmsg`` channel on the freenode network with a firehose bot echoing
messages to channel to help give you a feel for what's going on.

You can find the list of available topics in Fedora's infrastructure
at https://fedora-fedmsg.readthedocs.io

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

In a default configuration, sending a message looks like the following:

.. code-block:: python

   import fedmsg
   fedmsg.publish(topic='testing', modname='test', msg={
       'test': "Hello World",
   })

.. note:: The ``endpoints.py`` file should have an entry as ``"<myprogram>.<myhost>": [ ... ]`` where ``myprogram`` is
   the name of the program sending the message (can be ``__main__`` if it is a simple script) and ``myhost`` is the
   machine sending the program (corresponds to the output of ``hostname -s``).

If you need to publish to a specific endpoint or need a consistent endpoint, you'll need to pass the ``name`` parameter
and adjust the ``endpoints.py`` accordingly.

.. code-block:: python

   import fedmsg
   fedmsg.publish(name='mybus', topic='testing', modname='test', msg={
       'test': "Hello World",
   })

.. note:: The ``endpoints.py`` file should have an entry as ``"mybus": [ ... ]``

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
   compatibility
   config
   topics

----

.. note::
   :doc:`proposal` is a now out-moded document, but is kept here for historical
   purposes.
