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

import unittest

import os
import socket

from time import sleep, time
from uuid import uuid4

from moksha.hub.tests.test_hub import simulate_reactor
from moksha.hub.hub import MokshaHub
from moksha.hub import CentralMokshaHub
from fedmsg.core import FedMsgContext

from nose.tools import eq_, assert_true, assert_false, raises

import fedmsg.config
import fedmsg.consumers
import fedmsg.encoding


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

    # Enable all of our test consumers so they can do their thing.
    config['test_consumer_enabled'] = True

    # TODO -- this appears everywhere and should be encapsulated in a func
    # Massage the fedmsg config into the moksha config.
    config['zmq_subscribe_endpoints'] = ','.join(
        ','.join(bunch) for bunch in config['endpoints'].values()
    )
    hub_name = "twisted.%s" % socket.gethostname()
    config['zmq_publish_endpoints'] = ','.join(
        config['endpoints'][hub_name]
    )
    return config


# This used to raise a keyerror, but no longer.
@raises(KeyError)
def test_init_missing_endpoint():
    """ Try to initialize the context with a nonexistant service name. """
    config = load_config()
    config['name'] = "failboat"
    config['sign_messages'] = True
    context = FedMsgContext(**config)


class TestHub(unittest.TestCase):

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
            messages_received.append(fedmsg.encoding.loads(json.body))

        self.hub.subscribe(topic=self.fq_topic, callback=callback)
        sleep(sleep_duration)

        self.context.publish(topic=self.topic, msg=secret)

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        eq_(len(messages_received), 1)
        eq_(messages_received[0]['msg'], secret)

    def fake_register_consumer(self, cons):
        """ Fake register a consumer, not by entry-point like usual.

        Normally, consumers are identified by the hub by way of entry-points
        Ideally, this test would register the TestConsumer on the
        moksha.consumers entry point, and the hub would pick it up.
        I'm not sure how to do that, so we're going to fake it and manually
        add this consumer to the list of consumers of which the Hub is aware.
        """
        self.hub.topics[cons.topic] = self.hub.topics.get(cons.topic, [])
        self.hub.topics[cons.topic].append(cons(self.hub).consume)
        sleep(sleep_duration)

    def test_consumer(self):
        """ Check that a consumer can get messages. """
        obj = {'secret': secret}
        messages_received = []

        class TestConsumer(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

        self.fake_register_consumer(TestConsumer)

        # Now, send a generic message to that topic, and see if the consumer
        # processed it.
        fedmsg.publish(topic=self.topic, msg=obj)

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        eq_(len(messages_received), 1)
        eq_(messages_received[0], obj)

    def test_double_consumers(self):
        """ Check that two consumers can get messages. """
        obj = {'secret': secret}
        messages_received = []

        class TestConsumer1(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

        class TestConsumer2(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

        self.fake_register_consumer(TestConsumer1)
        self.fake_register_consumer(TestConsumer2)

        # Now, send a generic message to that topic, and see if the consumer
        # processed it.
        fedmsg.publish(topic=self.topic, msg=obj)

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        eq_(len(messages_received), 2)
        eq_(messages_received[0], obj)
        eq_(messages_received[1], obj)

    def test_consumer_failed_validation(self):
        """ Check that a consumer won't consume invalid message. """
        obj = {'secret': secret}
        messages_received = []

        class TestConsumer(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

            def validate(self, message):
                raise RuntimeWarning("Marking message as invalid.")

        self.fake_register_consumer(TestConsumer)
        fedmsg.publish(topic=self.topic, msg=obj)
        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        # Verify that we received no message.
        eq_(len(messages_received), 0)


if __name__ == '__main__':
    unittest.main()
