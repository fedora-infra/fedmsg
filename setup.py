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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110.15.0 USA
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
import os
import platform

data_config = {}

# We would set this up every time, but it results in an easy_install sandbox
# violation when fedmsg is installed as a dep from PyPI.  Consequently, we
# disable it unless the user explicitly asks for it.
if '--with-fedmsg-config' in sys.argv:
    # Specific the path for the config's file for some layout.
    # https://github.com/fedora-infra/fedmsg/issues/193
    list_fedmsgd = os.listdir('fedmsg.d')

    if 'VIRTUAL_ENV' in os.environ:
        path_config = os.environ['VIRTUAL_ENV'] + "/etc/fedmsg.d"
    else:
        if platform.system() == 'Windows':
            # Don't know the config path on Windows
            path_config = 'C:/fedmsg.d'
        else:
            path_config = '/etc/fedmsg.d'

    data_config = {'data_files': [(path_config, list_fedmsgd)]}

f = open('README.rst')
long_description = f.read().strip()
long_description = long_description.split('split here', 1)[1]
f.close()

install_requires = [
    'pyzmq',
    'kitchen',
    'requests',
    'six',
    'arrow',           # not *necessarily* required
]
extras_require = {
    'crypto': [
        # These are "optional" for now to make installation from pypi easier.
        'M2Crypto',    # for message validation
        'm2ext',       # for message validation
    ],
    'crypto_ng': [
        'cryptography>=1.6',
        'pyOpenSSL>=16.1.0',
    ],
    'commands': [
        'pygments',
        'psutil',
        'click',
    ],
    'consumers': [
        'moksha.hub>=1.3.0',
        'pygments',
        'psutil',
        # only needed for irc ssl support
        # 'pyopenssl',
        # 'service_identity',
    ],
}
extras_require['all'] = list(set(
    requirement
    for requirements in extras_require.values()
    for requirement in requirements
))
tests_require = [
    'moksha.hub',
    'pygments',
    'psutil',
    'sqlalchemy',  # For the persistent-store test(s).
]

if sys.version_info[0] == 2:
    tests_require.append('mock')


setup(
    name='fedmsg',
    version='1.1.1',
    description="Fedora Messaging Client API",
    long_description=long_description,
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='https://github.com/fedora-infra/fedmsg/',
    license='LGPLv2+',
    classifiers=[  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Networking',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    tests_require=tests_require,
    packages=[
        'fedmsg',
        'fedmsg.encoding',
        'fedmsg.commands',
        'fedmsg.consumers',
        # fedmsg.text is deprecated in favor of fedmsg.meta, but we'll leave it
        # around for backwards compatibility.  It's a symlink, for now.
        'fedmsg.text',
        'fedmsg.meta',
        'fedmsg.replay',
        'fedmsg.tests',
        'fedmsg.crypto'
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
            "fedmsg-logger=fedmsg.commands.logger:logger [commands]",
            "fedmsg-tail=fedmsg.commands.tail:tail [commands]",
            "fedmsg-collectd=fedmsg.commands.collectd:collectd [commands]",
            "fedmsg-announce=fedmsg.commands.announce:announce [commands]",
            "fedmsg-trigger=fedmsg.commands.trigger:trigger [commands]",
            "fedmsg-dg-replay=fedmsg.commands.replay:replay [commands]",
            "fedmsg-check=fedmsg.commands.check:check [commands]",
            # "fedmsg-config=fedmsg.commands.config:config [commands]",
            "fedmsg-hub=fedmsg.commands.hub:hub [consumers]",
            "fedmsg-relay=fedmsg.commands.relay:relay [consumers]",
            "fedmsg-signing-relay=fedmsg.commands.relay:signing_relay [consumers]",
            "fedmsg-gateway=fedmsg.commands.gateway:gateway [consumers]",
            "fedmsg-irc=fedmsg.commands.ircbot:ircbot [consumers]",
        ],
        'moksha.consumer': [
            "fedmsg-dummy=fedmsg.consumers.dummy:DummyConsumer [consumers]",
            "fedmsg-relay=fedmsg.consumers.relay:RelayConsumer [consumers]",
            "fedmsg-gateway=fedmsg.consumers.gateway:GatewayConsumer [consumers]",
            "fedmsg-ircbot=fedmsg.consumers.ircbot:IRCBotConsumer [consumers]",
        ],
        'moksha.producer': [
        ],
        # fedmsg core only provides one metadata provider.
        'fedmsg.meta': [
            "logger=fedmsg.meta.logger:LoggerProcessor",
            "announce=fedmsg.meta.announce:AnnounceProcessor",
        ],
    },
    **data_config
)
