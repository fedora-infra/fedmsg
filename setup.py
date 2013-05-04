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

try:
    from setuptools import setup
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup

import sys

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()

# Ridiculous as it may seem, we need to import multiprocessing and
# logging here in order to get tests to pass smoothly on python 2.7.
try:
    import multiprocessing
    import logging
except Exception:
    pass


install_requires = [
    'pyzmq',
    'fabulous',
    'kitchen',
    'moksha.hub>=1.2.0',
    'requests',
    'pygments',
    #'daemon',

    # These are "optional" for now to make installation from pypi easier.
    #'M2Crypto',
    #'m2ext',
]
tests_require = [
    'nose',
    'mock',
    'six',  # In the future, we'll use this across fedmsg proper for py3.
]

if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
    install_requires.extend([
        'argparse',
        'ordereddict',
        'logutils',
    ])
    tests_require.extend([
        'unittest2',
    ])


setup(
    name='fedmsg',
    version='0.6.8',
    description="Fedora Messaging Client API",
    long_description=long_description,
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='http://github.com/fedora-infra/fedmsg/',
    license='LGPLv2+',
    install_requires=install_requires,
    tests_require=tests_require,
    test_suite='nose.collector',
    packages=[
        'fedmsg',
        'fedmsg.encoding',
        'fedmsg.commands',
        'fedmsg.consumers',
        # fedmsg.text is deprecated in favor of fedmsg.meta, but we'll leave it
        # around for backwards compatibility.  It's a symlink, for now.
        'fedmsg.text',
        'fedmsg.meta',
        'fedmsg.tests',
    ],
    include_package_data=True,
    zip_safe=False,
    scripts=[
        # This is separate from the other console scripts just for efficiency's
        # sake.  It gets called over and over and over again by our mediawiki
        # plugin/mod_php.  By making it *not* a setuptools console_script it
        # does a lot less IO work to stand up.

        # Before:
        #   $ strace fedmsg-config 2>&1 | wc -l
        #   34843

        # After:
        #   $ strace fedmsg-config 2>&1 | wc -l
        #   13288

        'scripts/fedmsg-config',
    ],
    entry_points={
        'console_scripts': [
            "fedmsg-logger=fedmsg.commands.logger:logger",
            "fedmsg-tail=fedmsg.commands.tail:tail",
            "fedmsg-hub=fedmsg.commands.hub:hub",
            "fedmsg-relay=fedmsg.commands.relay:relay",
            "fedmsg-gateway=fedmsg.commands.gateway:gateway",
            #"fedmsg-config=fedmsg.commands.config:config",
            "fedmsg-irc=fedmsg.commands.ircbot:ircbot",
            "fedmsg-collectd=fedmsg.commands.collectd:collectd",
            "fedmsg-tweet=fedmsg.commands.tweet:tweet",
            "fedmsg-announce=fedmsg.commands.announce:announce",
        ],
        'moksha.consumer': [
            "fedmsg-dummy=fedmsg.consumers.dummy:DummyConsumer",
            "fedmsg-relay=fedmsg.consumers.relay:RelayConsumer",
            "fedmsg-gateway=fedmsg.consumers.gateway:GatewayConsumer",
            "fedmsg-ircbot=fedmsg.consumers.ircbot:IRCBotConsumer",
            "fedmsg-tweet=fedmsg.consumers.tweet:TweetBotConsumer",
        ],
        'moksha.producer': [
        ],
        # fedmsg core only provides one metadata provider.
        'fedmsg.meta': [
            "logger=fedmsg.meta.logger:LoggerProcessor",
            "announce=fedmsg.meta.announce:AnnounceProcessor",
        ],
    }
)
