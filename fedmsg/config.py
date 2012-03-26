""" Handles loading, processing and validation of all configuration.

Configuration values are determined by checking in the following order

    - Built-in defaults
    - Config file (/etc/fedmsg.ini)
    - Command line arguments

For example, if a config value does not appear in either the config file or on
the command line, then the built-in default is used.  If a value appears in
both the config file and as a command line argument, then the command line
value is used.
"""

import argparse
import collections
import copy
import inspect
import os
import pprint
import sys

import ConfigParser

defaults = dict(
    io_threads=1,
    topic_prefix="org.fedoraproject",
    post_init_sleep=0.5,
    timeout=2,
    print_config=False,
    high_water_mark=0,  # zero means no limit
)

__cache = {}


def load_config(extra_args,
                doc,
                filenames=None,
                invalidate_cache=False,
                fedmsg_command=False):
    """ Setup a config file from the following sources ordered by importance:

      - defaults
      - config file
      - command line arguments

    """
    global __cache

    if invalidate_cache:
        __cache = {}

    if __cache:
        return __cache

    config = copy.deepcopy(defaults)
    config.update(_process_config_file(filenames=filenames))

    # This is optional (and defaults to false) so that only 'fedmsg-*' commands
    # are required to provide these arguments.
    # For instance, the moksha-hub command takes a '-v' argument and internally
    # makes calls to fedmsg.  We don't want to impose all of fedmsg's CLI option
    # constraints on programs that use fedmsg, so we make it optional.
    if fedmsg_command:
        config.update(_process_arguments(extra_args, doc, config))

    # If the user specified a config file on the command line, then start over
    # but read in that file instead.
    if not filenames and config.get('config_filename', None):
        return load_config(extra_args, doc,
                           filenames=[config['config_filename']])

    # Do some post-load type massaging
    for args, kwargs in extra_args:
        # For arguments that accept multiple items (like a list of endpoints,
        # for instance), break those items down into lists from comma separated
        # strings.  That is, do so unless they are already lists.
        if kwargs.get('nargs', None) is '*' and \
           type(config[kwargs['dest']]) != list:
            config[kwargs['dest']] = [
                item.strip() for item in config[kwargs['dest']].split(',')
            ]

    # Just a little debug option.  :)
    if config['print_config']:
        pprint.pprint(config)
        sys.exit(0)

    __cache = config
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
    parser.add_argument(
        '--config-filename',
        dest='config_filename',
        help="Config file to use.",
        default=None,
    )
    parser.add_argument(
        '--print-config',
        dest='print_config',
        help='Simply print out the configuration and exit.  No action taken.',
        default=False,
        action='store_true',
    )
    parser.add_argument(
        '--timeout',
        dest='timeout',
        help="Timeout in seconds for any blocking zmq operations.",
        type=float,
        default=config['timeout'],
    )
    parser.add_argument(
        '--high-water-mark',
        dest='high_water_mark',
        help="Limit on the number of messages in the queue before blocking.",
        type=int,
        default=config['high_water_mark'],
    )

    for args, kwargs in declared_args:

        # Replace the hard-coded extra_args default with the config file value
        # (if it exists)
        if all([k in kwargs for k in ['dest', 'default']]):
            kwargs['default'] = config.get(
                kwargs['dest'], kwargs['default'])

        # Having slurped smart defaults from the config file, add the CLI arg.
        parser.add_argument(*args, **kwargs)

    args = parser.parse_args()
    return dict(args._get_kwargs())


def _process_config_file(filenames=None):

    filenames = filenames or []

    # Validate that these files are really files
    for fname in filenames:
        if not os.path.isfile(fname):
            raise ValueError("%r is not a file." % fname)

    # If nothing specified, look in the default locations
    if not filenames:
        filenames = [
            '/etc/fedmsg.ini',
            os.path.expanduser('~/.fedmsg.ini'),
            os.getcwd() + '/fedmsg.ini',
        ]

    parser = ConfigParser.SafeConfigParser()
    files = parser.read(filenames=filenames)

    config = {}
    if parser.has_section('fedmsg'):
        config = dict(parser.items('fedmsg'))

    return config
