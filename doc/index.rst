Fedora Infrastructure Message Bus
=================================

We want to hook all the services in Fedora Infrastructure up to send messages to
one another over a message bus instead of communicating with each other in
the heterogenous, "Rube-Goldberg" ways they do now.

``fedmsg`` (Fedora-Messaging) is a python package and API used around
Fedora Infrastructure to send and receive messages to and from applications.
See :doc:`overview` for a thorough introduction.

The quickest way to see what the bus is all about is to jump into
``#fedora-fedmsg`` on the freenode network.  There's a firehose bot there
echoing messages to channel.  It has a sister bot `running on identi.ca
<http://identi.ca/fedmsgbot>`_.

Publishing Messages with Python
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`development` on setting up your environment and workflow.

.. code-block:: python

   import fedmsg
   fedmsg.publish(topic='testing', modname='test', msg={
       'test': "Hello World",
   })

Publishing Messages from the Shell
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ echo "Hello World." | fedmsg-logger --modname=git --topic=repo.update
   $ echo '{"a": 1}' | fedmsg-logger --json-input
   $ fedmsg-logger --message="This is a message."
   $ fedmsg-logger --message='{"a": 1}' --json-input


Community
~~~~~~~~~

The source for this document can be found `on github
<http://github.com/fedora-infra/fedmsg>`_.  The issue tracker can be `found
there <http://github.com/fedora-infra/fedmsg/issues>`_, too.

Almost all discussion happens in ``#fedora-apps`` on the freenode network.
There is also a `mailing list
<https://admin.fedoraproject.org/mailman/listinfo/messaging-sig>`_ that
doesn't have much traffic.

Testimonials
------------

- `Jordan Sissel <http://www.semicomplete.com>`_ -- "Cool idea, gives new
  meaning to open infrastructure."
- `David Gay <http://oddshocks.com>`_ -- "It's like I'm working with software
  made by people who thought about the future."

Rough Outline of Stages of development/deployment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1) Start writing ``fedmsg`` core.
2) Use ``fedmsg`` to send messages from existing services (koji, bodhi,
   pkgdb, fas, etc...).  The status of this is kept in :doc:`status` and
   :doc:`topology`.
3) Consume messages for statistics, i.e. an independent statistics webapp.
   This will some day be the responsibility of `datanommer
   <http://github.com/fedora-infra/datanommer>`_.  See :doc:`status` for its
   status in our infrastructure.
4) Consume messages for user experience, i.e. any or all of rss, email,
   gnome-shell notifications, javascript notifications in FI webapps.  One
   example of this is `lmacken's <http://lewk.org>`_ dbus-based `fedmsg-notify
   <https://github.com/lmacken/fedmsg-notify>`_.
5) Consume messages for service interoperability: for example, have koji
   invalidate it's cache when it sees pkgdb messages go by on the bus.  Or,
   have the mirrors starts to sync once a new compose of branched or rawhide is
   complete.

   This comes last because we want to make sure that message-sending works
   and is reliable before we start making existing services depend on it
   for their functioning.

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
