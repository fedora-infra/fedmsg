Commands
========

Console Scripts
---------------

``fedmsg`` provides a number of console scripts for
use with random shell scripts.

fedmsg-logger
~~~~~~~~~~~~~

.. autofunction:: fedmsg.commands.logger.logger

fedmsg-tail
~~~~~~~~~~~

.. autofunction:: fedmsg.commands.tail.tail

fedmsg-dg-replay
~~~~~~~~~~~~~~~~

.. autofunction:: fedmsg.commands.replay.replay

fedmsg-collectd
~~~~~~~~~~~~~~~

.. autofunction:: fedmsg.commands.collectd.collectd

Service Daemons
---------------

fedmsg-hub
~~~~~~~~~~
.. autofunction:: fedmsg.commands.hub.hub

fedmsg-relay
~~~~~~~~~~~~
.. autofunction:: fedmsg.commands.relay.relay

fedmsg-irc
~~~~~~~~~~
.. autofunction:: fedmsg.commands.ircbot.ircbot

fedmsg-gateway
~~~~~~~~~~~~~~
.. autofunction:: fedmsg.commands.gateway.gateway

Writing your own fedmsg commands
--------------------------------

The :mod:`fedmsg.commands` module provides a ``@command`` decorator to help simplify this.

.. automodule:: fedmsg.commands
    :members:
    :undoc-members:
    :show-inheritance:

