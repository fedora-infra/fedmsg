# This file *was* a part of Moksha.
# Copyright (C) 2008-2010  Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import moksha
import unittest

import os

from time import sleep, time
from uuid import uuid4

from unittest import TestCase

from moksha.hub.reactor import reactor as _reactor
from moksha.hub.hub import MokshaHub
from nose.tools import eq_, assert_true, assert_false

import fedmsg.config


# Some constants used throughout the hub tests
sleep_duration = 0.25
secret = "secret_message"


def simulate_reactor(duration=sleep_duration):
    """ Simulate running the reactor for `duration` milliseconds """
    global _reactor
    start = time()
    while time() - start < duration:
        _reactor.doPoll(0.0001)
        _reactor.runUntilCurrent()


class TestHub(TestCase):

    def setUp(self):
        here = os.path.sep.join(__file__.split(os.path.sep)[:-1])
        test_config = os.path.sep.join([here, 'fedmsg-test-config.py'])

        config = fedmsg.config.load_config(
            [],
            "awesome",
            filenames=[
                test_config,
            ],
        )

        # TODO -- this appears everywhere and should be encapsulated in a func
        # Massage the fedmsg config into the moksha config.
        config['zmq_subscribe_endpoints'] = ','.join(
            ','.join(bunch) for bunch in config['endpoints'].values()
        )

        self.hub = MokshaHub(config=config)

    def tearDown(self):
        self.hub.close()

    def test_run_hub_get_heartbeat(self):
        """ Start the heartbeat producer and ensure it emits a message. """
        self.skipTest("Not implemented.")

    def test_send_recv(self):
        """ Send a message and receive it. """
        self.skipTest("Not implemented.")

