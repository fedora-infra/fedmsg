#!/usr/bin/env python

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
    'simplejson',
    'fabulous',
    'kitchen',
    'moksha>=0.8.6',
    #'daemon',
    'M2Crypto',
    'm2ext',
]

if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
    install_requires.append('argparse')
    install_requires.append('ordereddict')


setup(
    name='fedmsg',
    version='0.2.1',
    description="Fedora Messaging Client API",
    long_description=long_description,
    author='Ralph Bean',
    author_email='rbean@redhat.com',
    url='http://github.com/ralphbean/fedmsg/',
    license='LGPLv2+',
    install_requires=install_requires,
    tests_require=[
        'nose',
    ],
    test_suite='nose.collector',
    packages=[
        'fedmsg',
        'fedmsg.commands',
        'fedmsg.consumers',
        'fedmsg.producers',
        'fedmsg.tests',
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "fedmsg-logger=fedmsg.commands.logger:logger",
            "fedmsg-status=fedmsg.commands.status:status",
            "fedmsg-tail=fedmsg.commands.tail:tail",
            "fedmsg-hub=fedmsg.commands.hub:hub",
            "fedmsg-relay=fedmsg.commands.relay:relay",
            "fedmsg-config=fedmsg.commands.config:config",
            "fedmsg-irc=fedmsg.commands.ircbot:ircbot",
        ],
        'moksha.consumer': [
            "fedmsg-dummy=fedmsg.consumers.dummy:DummyConsumer",
            "fedmsg-relay=fedmsg.consumers.relay:RelayConsumer",
            "fedmsg-ircbot=fedmsg.consumers.ircbot:IRCBotConsumer",
        ],
        'moksha.producer': [
            "heartbeat=fedmsg.producers.heartbeat:HeartbeatProducer",
        ],
    }
)
