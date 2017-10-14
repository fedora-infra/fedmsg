# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
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
""" Tests for fedmsg.config """
import os
import unittest

import mock

import fedmsg.config
from fedmsg.tests.base import FIXTURES_DIR
from fedmsg.tests.common import load_config


class RecursiveUpdateBase(unittest.TestCase):
    originals = None
    expected = None

    def test_match(self):
        """ Does fedmsg.config._recursive_update produce the expected result?
        """

        if None in (self.originals, self.expected):
            return

        actual = dict()
        for o in self.originals:
            actual = fedmsg.config._recursive_update(actual, o)

        self.assertEqual(actual, self.expected)


class TestSimpleOne(RecursiveUpdateBase):
    originals = [dict(a=2)]
    expected = dict(a=2)


class TestSimpleTwo(RecursiveUpdateBase):
    originals = [
        dict(a=2),
        dict(b=3),
    ]
    expected = dict(a=2, b=3)


class TestOverwrite(RecursiveUpdateBase):
    originals = [
        dict(a=2),
        dict(a=3),
    ]
    expected = dict(a=3)


class TestMerge(RecursiveUpdateBase):
    originals = [
        dict(a=dict(a=2)),
        dict(a=dict(b=3)),
    ]
    expected = dict(a=dict(a=2, b=3))


class TestConfig(unittest.TestCase):
    """Test for try out the function iterate in
    endpoints config"""

    def test_config(self):
        config = load_config()
        endpoints = config['endpoints']

        for key, value in endpoints.items():
            assert isinstance(value, list), value


class GetConfigFilesTests(unittest.TestCase):
    """Tests for :func:`fedmsg.config._get_config_files`."""

    def test_config_file(self):
        """Assert a config file can be provided."""
        with mock.patch.dict(os.environ, {'FEDMSG_CONFIG': os.path.join(FIXTURES_DIR, 'conf.py')}):
            files = fedmsg.config._get_config_files()

        self.assertEqual([os.path.join(FIXTURES_DIR, 'conf.py')], files)

    def test_config_dir(self):
        """Assert a config directory can be provided."""
        with mock.patch.dict(os.environ, {'FEDMSG_CONFIG': os.path.join(FIXTURES_DIR, 'conf.d')}):
            files = fedmsg.config._get_config_files()

        self.assertEqual([os.path.join(FIXTURES_DIR, 'conf.d/conf1.py')], files)

    def test_empty_dir(self):
        """Assert an empty directory returns an empty list"""
        with mock.patch.dict(os.environ, {'FEDMSG_CONFIG': os.path.join(FIXTURES_DIR, 'empty.d')}):
            files = fedmsg.config._get_config_files()

        self.assertEqual([], files)

    @mock.patch('fedmsg.config.os.path.isfile', mock.Mock(return_value=False))
    @mock.patch('fedmsg.config.os.path.isdir', mock.Mock(return_value=False))
    @mock.patch('fedmsg.config._log')
    def test_no_file(self, mock_log):
        """Assert no files are handled gracefully, but gets logged"""
        files = fedmsg.config._get_config_files()

        self.assertEqual([], files)
        mock_log.info.assert_called_once_with(
            'No configuration files found in %s', '/etc/fedmsg.d')


class FedmsgConfigTests(unittest.TestCase):
    """Tests for :func:`fedmsg.config.FedmsgConfig`."""

    defaults = {
        'topic_prefix': 'com.example',
        'environment': 'dev',
        'io_threads': 1,
        'post_init_sleep': 0.5,
        'timeout': 2,
        'print_config': False,
        'high_water_mark': 0,
        # milliseconds
        'zmq_linger': 1000,
        'zmq_enabled': True,
        'zmq_strict': False,
        'zmq_tcp_keepalive': 1,
        'zmq_tcp_keepalive_cnt': 3,
        'zmq_tcp_keepalive_idle': 60,
        'zmq_tcp_keepalive_intvl': 5,
        'zmq_reconnect_ivl': 100,
        'zmq_reconnect_ivl_max': 1000,
        'endpoints': {
            'relay_outbound': [
                'tcp://127.0.0.1:4001',
            ]
        },
        'relay_inbound': 'tcp://127.0.0.1:2001',
        'fedmsg.consumers.gateway.port': 9940,
        'fedmsg.consumers.gateway.high_water_mark': 1000,
        'sign_messages': False,
        'validate_signatures': True,
        'crypto_backend': 'x509',
        'crypto_validate_backends': ['x509'],
        'ssldir': '/etc/pki/fedmsg',
        'crl_location': None,
        'crl_cache': None,
        'crl_cache_expiry': None,
        'ca_cert_location': '/etc/pki/fedmsg/ca.crt',
        'ca_cert_cache': None,
        'ca_cert_cache_expiry': None,
        'certnames': {},
        'routing_policy': {},
        'routing_nitpicky': False,
        'irc': [
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
        'irc_color_lookup': {
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
        'irc_default_color': 'light grey',
        'irc_method': 'notice',
        'active': False,
        'persistent_store': None,
        'logging': {
            'version': 1,
            'formatters': {
                'bare': {
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                    'format': "[%(asctime)s][%(name)10s %(levelname)7s] %(message)s"
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
        'stomp_uri': None,
        'stomp_user': None,
        'stomp_pass': None,
        'stomp_ssl_crt': None,
        'stomp_ssl_key': None,
        'datagrepper_url': None,
    }

    def test_defaults(self):
        """Assert there's a set of default configuration values."""
        conf = fedmsg.config.FedmsgConfig()

        for key in self.defaults:
            self.assertEqual(self.defaults[key], conf[key])

    @mock.patch('fedmsg.config._process_config_file')
    @mock.patch('fedmsg.config._get_config_files', mock.Mock(return_value=['/a', '/b']))
    def test_load_config_files(self, mock_process):
        conf = fedmsg.config.FedmsgConfig()
        mock_process.side_effect = [{'stomp_user': u'jcline'}, {'stomp_pass': u'hunter2'}]

        conf.copy()

        self.assertEqual(2, mock_process.call_count)
        self.assertEqual(u'jcline', conf['stomp_user'])
        self.assertEqual(u'hunter2', conf['stomp_pass'])

    def test_lazy_load_get(self):
        """Assert calling get loads the default config."""
        conf = fedmsg.config.FedmsgConfig()

        self.assertEqual({}, conf)
        conf.get('stomp_ssl_key')
        self.assertEqual(self.defaults, conf)

    def test_lazy_load_get_load_once(self):
        """Assert calling get multiple times loads the config once."""
        conf = fedmsg.config.FedmsgConfig()
        conf.load_config = mock.Mock(side_effect=conf.load_config)

        conf.get('stomp_ssl_key')
        conf.get('stomp_ssl_key')

        self.assertEqual(1, conf.load_config.call_count)

    def test_lazy_load_getitem(self):
        """Assert calling __getitem__ loads the default config."""
        conf = fedmsg.config.FedmsgConfig()

        self.assertEqual({}, conf)
        conf['stomp_ssl_key']
        self.assertEqual(self.defaults, conf)

    def test_lazy_load_getitem_load_once(self):
        """Assert calling getitem multiple times loads the config once."""
        conf = fedmsg.config.FedmsgConfig()
        conf.load_config = mock.Mock(side_effect=conf.load_config)

        conf['stomp_ssl_key']
        conf['stomp_ssl_key']

        self.assertEqual(1, conf.load_config.call_count)

    def test_lazy_load_copy_load_once(self):
        """Assert calling getitem multiple times loads the config once."""
        conf = fedmsg.config.FedmsgConfig()
        conf.load_config = mock.Mock(side_effect=conf.load_config)

        conf.copy()
        conf.copy()

        self.assertEqual(1, conf.load_config.call_count)

    def test_lazy_load_copy(self):
        """Assert calling copy loads the default config."""
        conf = fedmsg.config.FedmsgConfig()

        self.assertEqual({}, conf)
        self.assertEqual(self.defaults, conf.copy())
        self.assertEqual(self.defaults, conf)

    def test_load_config_settings(self):
        """Assert settings can be passed to the load_config method"""
        conf = fedmsg.config.FedmsgConfig()
        expected = self.defaults.copy()
        expected['stomp_ssl_key'] = u'/my/key'

        conf.load_config({'stomp_ssl_key': u'/my/key'})
        self.assertEqual(expected, conf)

    def test_true_string_bool_setting(self):
        """Assert true strings are converted to bool."""
        conf = fedmsg.config.FedmsgConfig()
        expected = self.defaults.copy()
        expected['active'] = True

        conf.load_config({'active': u' true'})
        self.assertEqual(expected, conf)

    def test_false_string_bool_setting(self):
        """Assert false strings are converted to bool."""
        conf = fedmsg.config.FedmsgConfig()
        expected = self.defaults.copy()
        expected['active'] = False

        conf.load_config({'active': u' FALSE '})
        self.assertEqual(expected, conf)

    def test_invalid_bool_setting(self):
        """Assert a helpful message is generated when the bool setting is unparsable."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'active': u'true on tuesdays'})
        self.assertEqual('Invalid configuration values were set: \n\tactive: "true on tuesdays"'
                         ' must be a boolean ("True" or "False")', str(cm.exception))

    def test_not_a_string_or_bool_setting(self):
        """Assert a helpful message is generated when the bool setting is an invalid type."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'active': dict()})
        self.assertEqual('Invalid configuration values were set: \n\tactive: "{}"'
                         ' is not a boolean value.', str(cm.exception))

    def test_invalid_int_setting(self):
        """Assert a helpful message is generated when an integer setting is unparsable."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'io_threads': 'one'})
        self.assertEqual('Invalid configuration values were set: \n\tio_threads: '
                         "invalid literal for int() with base 10: 'one'", str(cm.exception))

    def test_negative_int_setting(self):
        """Assert a helpful message is generated when an integer setting is negative."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'io_threads': -1})
        self.assertEqual('Invalid configuration values were set: \n\tio_threads: '
                         'Integer must be greater than or equal to zero', str(cm.exception))

    def test_invalid_float_setting(self):
        """Assert a helpful message is generated when an unparsable float is provided."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'post_init_sleep': 'one point one'})
        self.assertTrue(
            'Invalid configuration values were set: \n\tpost_init_sleep:' in str(cm.exception))

    def test_negative_float_setting(self):
        """Assert a helpful message is generated when a negative float is provided."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'post_init_sleep': -1})
        self.assertEqual('Invalid configuration values were set: \n\tpost_init_sleep: Floating '
                         'point number must be greater than or equal to zero', str(cm.exception))

    def test_invalid_type_setting(self):
        """Assert a helpful message is generated when an invalid type is used."""
        conf = fedmsg.config.FedmsgConfig()

        with self.assertRaises(ValueError) as cm:
            conf.load_config({'certnames': []})
        self.assertTrue(
            'Invalid configuration values were set: \n\tcertnames: ' in str(cm.exception))


if __name__ == '__main__':
    unittest.main()
