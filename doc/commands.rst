Console Scripts
---------------

It makes sense for ``fedmsg`` to also provide a number of console scripts for
use with random shell scripts or with nagios, for instance.

Currently we have implemented:

 - ``fedmsg-tail`` - watches all endpoints on the bus and prints each message to
   stdout.
 - ``fedmsg-logger`` - sends messages over the ``org.fedoraproject.dev.logger``
   topic.  This requires that an instance of ``fedmsg-relay`` be running
   *somewhere* and that it's inbound address be listed in ``fedmsg-config.py``.
 - ``fedmsg-relay`` - a service which binds to two ports, listens for messages
   on one and emits them on the other.  ``fedmsg-logger`` requires that an
   instance of ``fedmsg-relay`` be running *somewhere* and that it's inbound
   address be listed in ``fedmsg-config.py``.
 - ``fedmsg-hub`` - the all-purpose daemon.  This should be run on every host
   that has services which declare their own consumers.  ``fedmsg-hub`` will
   listen to every endpoint defined in ``/etc/fedmsg-config.py`` and forward
   messages in-process to the locally-declared consumers.

 TODO - add irc
 TODO - add gateway

TODO - autodoc all those commands
