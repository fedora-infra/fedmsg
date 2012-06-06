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

from moksha.tests.test_hub import simulate_reactor
from moksha.hub.hub import MokshaHub
from moksha.hub import CentralMokshaHub
from fedmsg.core import FedMsgContext

from nose.tools import eq_, assert_true, assert_false, raises

import fedmsg.config
import fedmsg.json
from fedmsg.producers.heartbeat import HeartbeatProducer


# Some constants used throughout the hub tests
sleep_duration = 0.25
secret = "secret_message"

def load_config(name='fedmsg-test-config.py'):
    here = os.path.sep.join(__file__.split(os.path.sep)[:-1])
    test_config = os.path.sep.join([here, name])

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
    config['zmq_publish_endpoints'] = ','.join(
        config['endpoints'].values()[1]
    )
    return config


@raises(KeyError)
def test_init_missing_endpoint():
    """ Try to initialize the context with a nonexistant service name. """
    config = load_config()
    config['name'] = "failboat"
    context = FedMsgContext(**config)


class TestHub(TestCase):

    def setUp(self):
        config = load_config()
        self.hub = CentralMokshaHub(config=config)
        self.context = FedMsgContext(**config)

        # fully qualified
        self.fq_topic = "org.fedoraproject.dev.unittest.foo"
        # short version
        self.topic = "foo"

    def tearDown(self):
        self.context.destroy()
        self.hub.close()

    def test_run_hub_get_heartbeat(self):
        """ Start the heartbeat producer and ensure it emits a message. """
        messages_received = []

        def callback(json):
            messages_received.append(fedmsg.json.loads(json.body))

        self.hub.subscribe(
            topic=HeartbeatProducer.topic,
            callback=callback,
        )

        simulate_reactor(HeartbeatProducer.frequency.seconds*1.1)
        sleep(HeartbeatProducer.frequency.seconds*1.1)

        eq_(len(messages_received), 1)

    def test_send_recv(self):
        """ Send a message and receive it.

        Admittedly, this is not a unit test, but an integration test.

        It tests:

            - Sending a message.
            - Receiving a message.
            - Encoding *and* decoding.

        """
        messages_received = []

        def callback(json):
            messages_received.append(fedmsg.json.loads(json.body))

        self.hub.subscribe(topic=self.fq_topic, callback=callback)
        sleep(sleep_duration)

        self.context.send_message(topic=self.topic, msg=secret)

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        eq_(len(messages_received), 1)
        eq_(messages_received[0]['msg'], secret)
