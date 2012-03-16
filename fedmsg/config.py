""" Handles loading, processing and validation of all configuration.

Configuration values are determined by checking in the following order

    - Built-in defaults
    - Config file (/etc/fedmsg.ini)
    - Command line arguments

For example, if a config value does not appear in either the config file or on
the command line, then the built-in default is used.  If a value appears in both
the config file and as a command line argument, then the command line value is
used.
"""

import argparse
import collections
import copy
import inspect
import os

import ConfigParser

# TODO -- centralize all defaults here
defaults = collections.OrderedDict(
    io_threads=1,
    topic_prefix="org.fedoraproject",
    post_init_sleep=0.5,
)


def load_config(extra_args, doc):
    config = copy.deepcopy(defaults)
    config.update(_process_config_file())
    config.update(_process_arguments(extra_args, doc, config))
    return config

def _process_arguments(declared_args, doc, config):
    parser = argparse.ArgumentParser(description=doc)

    parser.add_argument(
        '--io-threads',
        dest='io_threads',
        type=int,
        help="Number of io threads for 0mq to use",
        default=config['io_threads'],
    )
    parser.add_argument(
        '--topic-prefix',
        dest='topic_prefix',
        type=str,
        help="Prefix for the topic of each message sent.",
        default=config['topic_prefix'],
    )
    parser.add_argument(
        '--post-init-sleep',
        dest='post_init_sleep',
        type=float,
        help="Number of seconds to sleep after initializing.",
        default=config['post_init_sleep'],
    )

    for args, kwargs in declared_args:
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()
    return dict(args._get_kwargs())

def _process_config_file():
    parser = ConfigParser.ConfigParser(defaults=defaults)
    files = parser.read(filenames=[
        '/etc/fedmsg.ini',
        os.path.expanduser('~/.fedmsg.ini'),
        os.getcwd() + '/fedmsg.ini',
    ])
    return {}
