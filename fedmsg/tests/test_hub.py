# This file *was* a part of Moksha.
# Copyright (C) 2008 - 2014  Red Hat, Inc.
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

try:
    # For python-2.6, so we can do skipTest
    import unittest2 as unittest
except ImportError:
    import unittest

from time import sleep, time

from moksha.hub import CentralMokshaHub
from moksha.hub.reactor import reactor
from fedmsg.core import FedMsgContext

import fedmsg.config
import fedmsg.consumers
import fedmsg.encoding

from fedmsg.tests.common import load_config, requires_network


# Some constants used throughout the hub tests
sleep_duration = 0.25
secret = "secret_message"


def simulate_reactor(duration=sleep_duration):
    """ Simulate running the reactor for `duration` milliseconds """
    start = time()
    while time() - start < duration:
        reactor.doPoll(0.0001)
        reactor.runUntilCurrent()


class FedMsgContextTests(unittest.TestCase):

    def test_init_missing_cert(self):
        """ Try to initialize the context with a nonexistant cert. """
        config = load_config()
        config['name'] = "failboat"
        config['sign_messages'] = True
        with self.assertRaises(KeyError):
            context = FedMsgContext(**config)
            context.publish(topic='awesome', msg=dict(foo='bar'))


class TestHub(unittest.TestCase):

    def setUp(self):
        config = load_config()
        self.hub = CentralMokshaHub(config=config)
        self.context = FedMsgContext(**config)

        # fully qualified
        self.fq_topic = "org.fedoraproject.dev.%s.foo" % unittest.__name__
        # short version
        self.topic = "foo"

    def tearDown(self):
        self.context.destroy()
        self.hub.close()

    @requires_network
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

        self.assertEqual(len(messages_received), 1)
        self.assertEqual(messages_received[0]['msg'], secret)

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

    @requires_network
    def test_consumer(self):
        """ Check that a consumer can get messages. """
        obj = {'secret': secret}
        messages_received = []

        class TestConsumer(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def _consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

        self.fake_register_consumer(TestConsumer)

        # Now, send a generic message to that topic, and see if the consumer
        # processed it.
        self.context.publish(topic=self.topic, msg=obj)

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)
        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        self.assertEqual(len(messages_received), 1)
        self.assertEqual(messages_received[0], obj)

    @requires_network
    def test_double_consumers(self):
        """ Check that two consumers can get messages. """
        obj = {'secret': secret}
        messages_received = []

        class TestConsumer1(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def _consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

        class TestConsumer2(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def _consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

        self.fake_register_consumer(TestConsumer1)
        self.fake_register_consumer(TestConsumer2)

        # Now, send a generic message to that topic, and see if the consumer
        # processed it.
        self.context.publish(topic=self.topic, msg=obj)

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        self.assertEqual(len(messages_received), 2)
        self.assertEqual(messages_received[0], obj)
        self.assertEqual(messages_received[1], obj)

    @requires_network
    def test_consumer_failed_validation(self):
        """ Check that a consumer won't consume invalid message. """

        # TODO -- now that moksha.hub is doing its internal threading/queueing
        # behavior, this feature of fedmsg is a bit more difficult to test.
        raise self.skipTest("Not sure how to test this behavior now.")

        obj = {'secret': secret}
        messages_received = []

        class TestConsumer(fedmsg.consumers.FedmsgConsumer):
            topic = self.fq_topic
            config_key = "test_consumer_enabled"

            def _consume(self, message):
                messages_received.append(
                    message['body']['msg']
                )

            def validate(self, message):
                raise RuntimeWarning("Marking message as invalid.")

        self.fake_register_consumer(TestConsumer)
        self.context.publish(topic=self.topic, msg=obj)
        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        # Verify that we received no message.
        self.assertEqual(len(messages_received), 0)


if __name__ == '__main__':
    unittest.main()
