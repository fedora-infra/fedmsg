"""
The ``fedmsg`` `Click`_ CLI.

.. note:: Do not add commands to this module - each command should have its
          own module.

.. _Click: http://click.pocoo.org/
"""
import click


@click.group()
def cli():
    """
    The fedmsg command line interface.

    This can be used to run fedmsg services, check on the status of those services,
    publish messages, and more.
    """
    pass
