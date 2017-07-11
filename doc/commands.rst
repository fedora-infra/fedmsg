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

fedmsg-check
~~~~~~~~~~~~

``fedmsg-check`` is used to check the status of consumers and producers. It
requires the ``moksha.monitoring.socket`` key to be set in the configuration.

See usage details with ``fedmsg-check --help``.

Service Daemons
---------------

fedmsg-hub
~~~~~~~~~~
.. autofunction:: fedmsg.commands.hub.hub

fedmsg-relay
~~~~~~~~~~~~
.. autofunction:: fedmsg.commands.relay.relay

fedmsg-signing-relay
~~~~~~~~~~~~~~~~~~~~
.. autofunction:: fedmsg.commands.relay.signing_relay

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

