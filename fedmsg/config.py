# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#
"""
This module handles loading, processing and validation of all configuration.

The configuration values used at runtime are determined by checking in
the following order:

    - Built-in defaults
    - All Python files in the /etc/fedmsg.d/ directory
    - All Python files in the ~/.fedmsg.d/ directory
    - All Python files in the current working directory's fedmsg.d/ directory
    - Command line arguments

For example, if a config value does not appear in either the config file or on
the command line, then the built-in default is used.  If a value appears in
both the config file and as a command line argument, then the command line
value is used.

You can print the runtime configuration to the terminal by using the
``fedmsg-config`` command implemented by
:func:`fedmsg.commands.config.config`.
"""

import argparse
import copy
import logging
import os
import sys
import textwrap
import warnings

import six

from kitchen.iterutils import iterate
from fedmsg.encoding import pretty_dumps


_log = logging.getLogger(__name__)


bare_format = "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"


def _get_config_files():
    """
    Load the list of file paths for fedmsg configuration files.

    Returns:
        list: List of files containing fedmsg configuration.
    """
    config_paths = []
    if os.environ.get('FEDMSG_CONFIG'):
        config_location = os.environ['FEDMSG_CONFIG']
    else:
        config_location = '/etc/fedmsg.d'

    if os.path.isfile(config_location):
        config_paths.append(config_location)
    elif os.path.isdir(config_location):
        # list dir and add valid files
        possible_config_files = [os.path.join(config_location, p)
                                 for p in os.listdir(config_location) if p.endswith('.py')]
        for p in possible_config_files:
            if os.path.isfile(p):
                config_paths.append(p)
    if not config_paths:
        _log.info('No configuration files found in %s', config_location)
    return config_paths


def _validate_non_negative_int(value):
    """
    Assert a value is a non-negative integer.

    Returns:
        int: A non-negative integer number.

    Raises:
        ValueError: if the value can't be cast to an integer or is less than 0.
    """
    value = int(value)
    if value < 0:
        raise ValueError('Integer must be greater than or equal to zero')
    return value


def _validate_non_negative_float(value):
    """
    Assert a value is a non-negative float.

    Returns:
        float: A non-negative floating point number.

    Raises:
        ValueError: if the value can't be cast to an float or is less than 0.
    """
    value = float(value)
    if value < 0:
        raise ValueError('Floating point number must be greater than or equal to zero')
    return value


def _validate_none_or_type(t):
    """
    Create a validator that checks if a setting is either None or a given type.

    Args:
        t: The type to assert.

    Returns:
        callable: A callable that will validate a setting for that type.
    """
    def _validate(setting):
        """
        Check the setting to make sure it's the right type.

        Args:
            setting (object): The setting to check.

        Returns:
            object: The unmodified object if it's the proper type.

        Raises:
            ValueError: If the setting is the wrong type.
        """
        if setting is not None and not isinstance(setting, t):
            raise ValueError('"{}" is not "{}"'.format(setting, t))
        return setting
    return _validate


def _validate_bool(value):
    """
    Validate a setting is a bool.

    Returns:
        bool: The value as a boolean.

    Raises:
        ValueError: If the value can't be parsed as a bool string or isn't already bool.
    """
    if isinstance(value, six.text_type):
        if value.strip().lower() == 'true':
            value = True
        elif value.strip().lower() == 'false':
            value = False
        else:
            raise ValueError('"{}" must be a boolean ("True" or "False")'.format(value))

    if not isinstance(value, bool):
        raise ValueError('"{}" is not a boolean value.'.format(value))

    return value


class FedmsgConfig(dict):
    """
    The fedmsg configuration dictionary.

    To access the actual configuration, use the :data:`conf` instance of this
    class.
    """
    _loaded = False
    _defaults = {
        'topic_prefix': {
            'default': u'com.example',
            'validator': _validate_none_or_type(six.text_type),
        },
        'environment': {
            'default': u'dev',
            'validator': _validate_none_or_type(six.text_type),
        },
        'io_threads': {
            'default': 1,
            'validator': _validate_non_negative_int,
        },
        'post_init_sleep': {
            'default': 0.5,
            'validator': _validate_non_negative_float,
        },
        'timeout': {
            'default': 2,
            'validator': _validate_non_negative_int,
        },
        'print_config': {
            'default': False,
            'validator': _validate_bool,
        },
        'high_water_mark': {
            'default': 0,
            'validator': _validate_non_negative_int,
        },
        # milliseconds
        'zmq_linger': {
            'default': 1000,
            'validator': _validate_non_negative_int,
        },
        'zmq_enabled': {
            'default': True,
            'validator': _validate_bool,
        },
        'zmq_strict': {
            'default': False,
            'validator': _validate_bool,
        },
        'zmq_tcp_keepalive': {
            'default': 1,
            'validator': _validate_non_negative_int,
        },
        'zmq_tcp_keepalive_cnt': {
            'default': 3,
            'validator': _validate_non_negative_int,
        },
        'zmq_tcp_keepalive_idle': {
            'default': 60,
            'validator': _validate_non_negative_int,
        },
        'zmq_tcp_keepalive_intvl': {
            'default': 5,
            'validator': _validate_non_negative_int,
        },
        'zmq_reconnect_ivl': {
            'default': 100,
            'validator': _validate_non_negative_int,
        },
        'zmq_reconnect_ivl_max': {
            'default': 1000,
            'validator': _validate_non_negative_int,
        },
        'endpoints': {
            'default': {
                'relay_outbound': [
                    'tcp://127.0.0.1:4001',
                ]
            },
            'validator': None,
        },
        'relay_inbound': {
            'default': u'tcp://127.0.0.1:2001',
            'validator': _validate_none_or_type(six.text_type),
        },
        'fedmsg.consumers.gateway.port': {
            'default': 9940,
            'validator': _validate_non_negative_int,
        },
        'fedmsg.consumers.gateway.high_water_mark': {
            'default': 1000,
            'validator': _validate_non_negative_int,
        },
        'sign_messages': {
            'default': False,
            'validator': _validate_bool,
        },
        'validate_signatures': {
            'default': True,
            'validator': _validate_bool,
        },
        'crypto_backend': {
            'default': u'x509',
            'validator': _validate_none_or_type(six.text_type),
        },
        'crypto_validate_backends': {
            'default': ['x509'],
            'validator': _validate_none_or_type(list),
        },
        'ssldir': {
            'default': u'/etc/pki/fedmsg',
            'validator': _validate_none_or_type(six.text_type),
        },
        'crl_location': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'crl_cache': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'crl_cache_expiry': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'ca_cert_location': {
            'default': u'/etc/pki/fedmsg/ca.crt',
            'validator': _validate_none_or_type(six.text_type),
        },
        'ca_cert_cache': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'ca_cert_cache_expiry': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'certnames': {
            'default': {},
            'validator': _validate_none_or_type(dict),
        },
        'routing_policy': {
            'default': {},
            'validator': _validate_none_or_type(dict),
        },
        'routing_nitpicky': {
            'default': False,
            'validator': _validate_bool,
        },
        'irc': {
            'default': [
                {
                    'network': 'irc.freenode.net',
                    'port': 6667,
                    'ssl': False,
                    'nickname': 'fedmsg-dev',
                    'channel': 'my-fedmsg-channel',
                    'timeout': 120,
                    'make_pretty': True,
                    'make_terse': True,
                    'make_short': True,
                    'line_rate': 0.9,
                    'filters': {
                        'topic': [],
                        'body': ['lub-dub'],
                    },
                },
            ],
            'validator': _validate_none_or_type(list),
        },
        'irc_color_lookup': {
            'default': {
                'fas': 'light blue',
                'bodhi': 'green',
                'git': 'red',
                'tagger': 'brown',
                'wiki': 'purple',
                'logger': 'orange',
                'pkgdb': 'teal',
                'buildsys': 'yellow',
                'planet': 'light green',
            },
            'validator': _validate_none_or_type(dict),
        },
        'irc_default_color': {
            'default': u'light grey',
            'validator': _validate_none_or_type(six.text_type),
        },
        'irc_method': {
            'default': u'notice',
            'validator': _validate_none_or_type(six.text_type),
        },
        'active': {
            'default': False,
            'validator': _validate_bool,
        },
        'persistent_store': {
            'default': None,
            'validator': None,
        },
        'logging': {
            'default': {
                'version': 1,
                'formatters': {
                    'bare': {
                        "datefmt": "%Y-%m-%d %H:%M:%S",
                        "format": bare_format
                    },
                },
                'handlers': {
                    'console': {
                        "class": "logging.StreamHandler",
                        "formatter": "bare",
                        "level": "INFO",
                        "stream": "ext://sys.stdout",
                    }
                },
                'loggers': {
                    'fedmsg': {
                        "level": "INFO",
                        "propagate": False,
                        "handlers": ["console"],
                    },
                    'moksha': {
                        "level": "INFO",
                        "propagate": False,
                        "handlers": ["console"],
                    },
                },
            },
            'validator': _validate_none_or_type(dict),
        },
        'stomp_uri': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_user': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_pass': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_ssl_crt': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'stomp_ssl_key': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
        'datagrepper_url': {
            'default': None,
            'validator': _validate_none_or_type(six.text_type),
        },
    }

    def __getitem__(self, *args, **kw):
        """Load the configuration if necessary and forward the call to the parent."""
        if not self._loaded:
            self.load_config()
        return super(FedmsgConfig, self).__getitem__(*args, **kw)

    def get(self, *args, **kw):
        """Load the configuration if necessary and forward the call to the parent."""
        if not self._loaded:
            self.load_config()
        return super(FedmsgConfig, self).get(*args, **kw)

    def copy(self, *args, **kw):
        """Load the configuration if necessary and forward the call to the parent."""
        if not self._loaded:
            self.load_config()
        return super(FedmsgConfig, self).copy(*args, **kw)

    def load_config(self, settings=None):
        """
        Load the configuration either from the config file, or from the given settings.

        Args:
            settings (dict): If given, the settings are pulled from this dictionary. Otherwise, the
                config file is used.
        """
        self._load_defaults()
        if settings:
            self.update(settings)
        else:
            config_paths = _get_config_files()
            for p in config_paths:
                conf = _process_config_file([p])
                self.update(conf)
        self._loaded = True
        self._validate()

    def _load_defaults(self):
        """Iterate over self._defaults and set all default values on self."""
        for k, v in self._defaults.items():
            self[k] = v['default']

    def _validate(self):
        """
        Run the validators found in self._defaults on all the corresponding values.

        Raises:
            ValueError: If the configuration contains an invalid configuration value.
        """
        errors = []
        for k in self._defaults.keys():
            try:
                validator = self._defaults[k]['validator']
                if validator is not None:
                    self[k] = validator(self[k])
            except ValueError as e:
                errors.append('\t{}: {}'.format(k, six.text_type(e)))

        if errors:
            raise ValueError(
                'Invalid configuration values were set: \n{}'.format('\n'.join(errors)))


#: The fedmsg configuration dictionary. All valid configuration keys are
#: guaranteed to be in the dictionary and to have a valid value. This dictionary
#: should not be mutated. This is meant to replace the old :func:`load_config`
#: API, but is not backwards-compatible with it.
conf = FedmsgConfig()


defaults = dict(
    topic_prefix="org.fedoraproject",
    environment="dev",
    io_threads=1,
    post_init_sleep=0.5,
    timeout=2,
    print_config=False,
    high_water_mark=0,  # zero means no limit
    zmq_linger=1000,    # Wait one second before timing out on fedmsg-relay
    active=False,       # if active, "connect", else "bind"
                        # Generally active is true only for fedmsg-logger
    persistent_store=None,  # an object.  See the fedmsg.replay module.
    logging=dict(
        version=1,
        formatters=dict(
            bare={
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "format": bare_format
            },
        ),
        handlers=dict(
            console={
                "class": "logging.StreamHandler",
                "formatter": "bare",
                "level": "INFO",
                "stream": "ext://sys.stdout",
            }
        ),
        loggers=dict(
            fedmsg={
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
            moksha={
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
        ),
    ),
)

__cache = {}


def load_config(extra_args=None,
                doc=None,
                filenames=None,
                invalidate_cache=False,
                fedmsg_command=False,
                disable_defaults=False):
    """ Setup a runtime config dict by integrating the following sources
    (ordered by precedence):

      - defaults (unless disable_defaults = True)
      - config file
      - command line arguments

    If the ``fedmsg_command`` argument is False, no command line arguments are
    checked.

    """
    warnings.warn('Using "load_config" is deprecated and will be removed in a future release;'
                  ' use the "fedmsg.config.conf" dictionary instead.', DeprecationWarning)
    global __cache

    if invalidate_cache:
        __cache = {}

    if __cache:
        return __cache

    # Coerce defaults if arguments are not supplied.
    extra_args = extra_args or []
    doc = doc or ""

    if not disable_defaults:
        config = copy.deepcopy(defaults)
    else:
        config = {}

    config.update(_process_config_file(filenames=filenames))

    # This is optional (and defaults to false) so that only 'fedmsg-*' commands
    # are required to provide these arguments.
    # For instance, the moksha-hub command takes a '-v' argument and internally
    # makes calls to fedmsg.  We don't want to impose all of fedmsg's CLI
    # option constraints on programs that use fedmsg, so we make it optional.
    if fedmsg_command:
        config.update(_process_arguments(extra_args, doc, config))

    # If the user specified a config file on the command line, then start over
    # but read in that file instead.
    if not filenames and config.get('config_filename', None):
        return load_config(extra_args, doc,
                           filenames=[config['config_filename']],
                           fedmsg_command=fedmsg_command,
                           disable_defaults=disable_defaults)

    # Just a little debug option.  :)
    if config.get('print_config'):
        print(pretty_dumps(config))
        sys.exit(0)

    if not disable_defaults and 'endpoints' not in config:
        raise ValueError("No config value 'endpoints' found.")

    if not isinstance(config.get('endpoints', {}), dict):
        raise ValueError("The 'endpoints' config value must be a dict.")

    if 'endpoints' in config:
        config['endpoints'] = dict([
            (k, list(iterate(v))) for k, v in config['endpoints'].items()
        ])

    if 'srv_endpoints' in config and len(config['srv_endpoints']) > 0:
        from dns.resolver import query, NXDOMAIN, Timeout, NoNameservers
        for e in config['srv_endpoints']:
            urls = []
            try:
                records = query('_fedmsg._tcp.{0}'.format(e), 'SRV')
            except NXDOMAIN:
                warnings.warn("There is no appropriate SRV records " +
                              "for {0}".format(e))
                continue
            except Timeout:
                warnings.warn("The DNS query for the SRV records of" +
                              " {0} timed out.".format(e))
                continue
            except NoNameservers:
                warnings.warn("No name server is available, please " +
                              "check the configuration")
                break

            for rec in records:
                urls.append('tcp://{hostname}:{port}'.format(
                    hostname=rec.target.to_text(),
                    port=rec.port
                ))
            config['endpoints'][e] = list(iterate(urls))

    if 'topic_prefix_re' not in config and 'topic_prefix' in config:
        # Turn "org.fedoraproject" into "org\.fedoraproject\.[^\W\d_]+"
        config['topic_prefix_re'] = config['topic_prefix'].replace('.', '\.')\
            + '\.[^\W\d_]+'

    __cache = config
    return config


def build_parser(declared_args, doc, config=None, prog=None):
    """ Return the global :class:`argparse.ArgumentParser` used by all fedmsg
    commands.

    Extra arguments can be supplied with the `declared_args` argument.
    """

    config = config or copy.deepcopy(defaults)
    prog = prog or sys.argv[0]

    parser = argparse.ArgumentParser(
        description=textwrap.dedent(doc),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=prog,
    )

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
    parser.add_argument(
        '--linger',
        dest='zmq_linger',
        help="Number of milliseconds to wait before timing out connections.",
        type=int,
        default=config['zmq_linger'],
    )

    for args, kwargs in declared_args:
        # Replace the hard-coded extra_args default with the config file value
        # (if it exists)
        if all([k in kwargs for k in ['dest', 'default']]):
            kwargs['default'] = config.get(
                kwargs['dest'], kwargs['default'])

        # Having slurped smart defaults from the config file, add the CLI arg.
        parser.add_argument(*args, **kwargs)

    return parser


def _process_arguments(declared_args, doc, config):
    parser = build_parser(declared_args, doc, config)
    args = parser.parse_args()
    return dict(args._get_kwargs())


def _gather_configs_in(directory):
    """ Return list of fully qualified python filenames in the given dir """
    try:
        return sorted([
            os.path.join(directory, fname)
            for fname in os.listdir(directory)
            if fname.endswith('.py')
        ])
    except OSError:
        return []


def _recursive_update(d1, d2):
    """ Little helper function that does what d1.update(d2) does,
    but works nice and recursively with dicts of dicts of dicts.

    It's not necessarily very efficient.
    """

    for k in set(d1).intersection(d2):
        if isinstance(d1[k], dict) and isinstance(d2[k], dict):
            d1[k] = _recursive_update(d1[k], d2[k])
        else:
            d1[k] = d2[k]

    for k in set(d2).difference(d1):
        d1[k] = d2[k]

    return d1


def execfile(fname, variables):
    """ This is builtin in python2, but we have to roll our own on py3. """
    with open(fname) as f:
        code = compile(f.read(), fname, 'exec')
        exec(code, variables)


def _process_config_file(filenames=None):

    filenames = filenames or []

    # Validate that these files are really files
    for fname in filenames:
        if not os.path.isfile(fname):
            raise ValueError("%r is not a file." % fname)

    # If nothing specified, look in the default locations
    if not filenames:
        filenames = [
            '/etc/fedmsg-config.py',
            os.path.expanduser('~/.fedmsg-config.py'),
            os.getcwd() + '/fedmsg-config.py',
        ]
        folders = ["/etc/fedmsg.d/", os.path.expanduser('~/.fedmsg.d/'),
                   os.getcwd() + '/fedmsg.d/', ]
        if 'VIRTUAL_ENV' in os.environ:
            folders.append(os.path.join(
                os.environ['VIRTUAL_ENV'], 'etc/fedmsg.d'))

        filenames = sum(map(_gather_configs_in, folders), []) + filenames

    # Each .ini file should really be a python module that
    # builds a config dict.
    config = {}
    for fname in filenames:
        if os.path.isfile(fname):
            variables = {}
            try:
                execfile(fname, variables)
                config = _recursive_update(config, variables['config'])
            except IOError as e:
                warnings.warn(str(e))

    return config
