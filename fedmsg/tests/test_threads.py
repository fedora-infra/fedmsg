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

try:
    # For python-2.6, so we can do skipTest
    import unittest2 as unittest
except ImportError:
    import unittest

import threading
import copy
import os
import socket

from time import sleep

from moksha.hub.tests.test_hub import simulate_reactor
from moksha.hub import CentralMokshaHub
from fedmsg.tests.common import requires_network

from nose.tools import eq_

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
        invalidate_cache=True
    )

    # TODO -- this appears everywhere and should be encapsulated in a func
    # Massage the fedmsg config into the moksha config.
    config['zmq_subscribe_endpoints'] = ','.join(
        ','.join(bunch) for bunch in config['endpoints'].values()
    )
    hub_name = "twisted.%s" % socket.gethostname().split('.', 1)[0]
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
        self.fq_topic = "org.fedoraproject.dev.threadtest.foo"
        # short version
        self.topic = "foo"

    def tearDown(self):
        self.hub.close()

    @requires_network
    def test_multi_threaded(self):
        """ Send messages from 5 concurrent threads. """
        messages_received = []

        def callback(json):
            messages_received.append(fedmsg.encoding.loads(json.body))

        self.hub.subscribe(topic=self.fq_topic, callback=callback)
        sleep(sleep_duration)

        test_name = "__main__.%s" % socket.gethostname().split('.', 1)[0]
        self.config['name'] = test_name

        class Publisher(threading.Thread):
            def run(shmelf):
                config = copy.deepcopy(self.config)
                import fedmsg
                fedmsg.init(**config)
                fedmsg.publish(topic=self.topic, msg=secret,
                               modname="threadtest")

        threads = [Publisher() for i in range(5)]
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        simulate_reactor(sleep_duration)
        sleep(sleep_duration)

        eq_(len(messages_received), 5)
        eq_(messages_received[0]['msg'], secret)

    def test_reinitialize(self):
        """ In a thread, try to destroy and re-init the API. """

        test_name = "__main__.%s" % socket.gethostname().split('.', 1)[0]
        self.config['name'] = test_name

        self.test_reinit_success = False

        class Publisher(threading.Thread):
            def run(shmelf):
                config = copy.deepcopy(self.config)
                import fedmsg
                fedmsg.init(**config)
                fedmsg.destroy()
                fedmsg.init(**config)
                fedmsg.destroy()
                fedmsg.init(**config)
                fedmsg.destroy()
                self.test_reinit_success = True

        thread = Publisher()
        thread.start()
        thread.join()

        assert(self.test_reinit_success)

if __name__ == '__main__':
    unittest.main()
