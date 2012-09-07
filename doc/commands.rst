Console Scripts
===============

``fedmsg`` provides a number of console scripts for
use with random shell scripts.

fedmsg-logger
-------------

.. autofunction:: fedmsg.commands.logger.logger

fedmsg-tail
-----------

.. autofunction:: fedmsg.commands.tail.tail

Service Daemons
===============

 - ``fedmsg-hub`` - the all-purpose daemon.  This should be run on every host
   that has services which declare their own consumers.  ``fedmsg-hub`` will
   listen to every endpoint discovered by :mod:`fedmsg.config` and forward
   messages in-process to the locally-declared consumers.
 - ``fedmsg-relay`` - a service which binds to two ports, listens for messages
   on one and emits them on the other.  ``fedmsg-logger`` requires that an
   instance of ``fedmsg-relay`` be running *somewhere* and that it's inbound
   address be listed in the config as :term:`relay_inbound`.

 TODO - add irc
 TODO - add gateway

TODO - autodoc all those commands

Writing your own fedmsg commands
================================

The :mod:`fedmsg.commands` module provides an ``@command`` decorator to help simplify this.

.. automodule:: fedmsg.commands
    :members:
    :undoc-members:
    :show-inheritance:

