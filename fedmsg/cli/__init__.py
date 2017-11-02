"""
The ``fedmsg`` `Click`_ CLI.

.. note:: Do not add commands to this module - each command should have its
          own module.

.. _Click: http://click.pocoo.org/
"""
import click

from fedmsg import config


@click.group()
@click.option('--conf', envvar='FEDMSG_CONFIG')
def cli(conf):
    """
    The fedmsg command line interface.

    This can be used to run fedmsg services, check on the status of those services,
    publish messages, and more.

    Note: This command-line interface is experimental and may change without a major
    release.
    """
    if conf:
        try:
            override_conf = config._process_config_file([conf])
            config.conf.load_config(settings=override_conf)
        except ValueError as e:
            raise click.exceptions.BadParameter(e)


from . import broker  # noqa
