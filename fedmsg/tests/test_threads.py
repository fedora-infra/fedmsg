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
import threading
import copy
import os
import socket

from time import sleep, time
from uuid import uuid4

from moksha.tests.test_hub import simulate_reactor
from moksha.hub.hub import MokshaHub
from moksha.hub import CentralMokshaHub
from fedmsg.core import FedMsgContext

from nose.tools import eq_, assert_true, assert_false, raises

import fedmsg.config
import fedmsg.consumers
import fedmsg.encoding
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
    hub_name = "twisted.%s" % socket.gethostname()
    config['zmq_publish_endpoints'] = ','.join(
        config['endpoints'][hub_name]
    )
    config['sign_messages'] = False
    return config


class TestHub(unittest.TestCase):

    def setUp(self):
        config = load_config()
        self.config = config
        self.hub = CentralMokshaHub(config=config)

        # fully qualified
        self.fq_topic = "org.fedoraproject.dev.unittest.foo"
        # short version
        self.topic = "foo"

    def tearDown(self):
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

        test_name = "__main__.%s" % socket.gethostname()
        self.config['name'] = test_name
        class Publisher(threading.Thread):
            def run(shmelf):
                config = copy.deepcopy(self.config)
                import fedmsg
                fedmsg.init(**config)
                try:
                    fedmsg.publish(topic=self.topic, msg=secret,
                                   modname="unittest")
                except Exception as e:
                    if hasattr(fedmsg.__local, '__context'):
                        fedmsg.__local.__context.destroy()

                    raise e

        threads = [Publisher() for i in range(5)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        eq_(len(messages_received), 5)
        eq_(messages_received[0]['msg'], secret)


if __name__ == '__main__':
    unittest.main()
