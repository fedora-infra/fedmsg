import unittest

import mock
import warnings
from fedmsg.core import FedMsgContext
from common import load_config


class TestCore(unittest.TestCase):
    def setUp(self):
        config = load_config()
        config['io_threads'] = 1
        self.ctx = FedMsgContext(**config)

    def test_send_message(self):
        """send_message is deprecated

        It tests
        - deprecation warning showing up appropriately
        - that we call publish method behind the scene
        """
        fake_topic = "org.fedoraproject.prod.compose.rawhide.complete"
        fake_msg = "{'arch'': 's390', 'branch': 'rawhide', 'log': 'done'}"
        self.ctx.publish = mock.Mock(spec_set=FedMsgContext.publish)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            self.ctx.send_message(topic=fake_topic, msg=fake_msg)
            assert len(w) == 1
            assert str(w[0].message) == ".send_message is deprecated."
            assert self.ctx.publish.called
            topic, msg, modname = self.ctx.publish.call_args[0]
            assert topic == fake_topic
            assert msg == fake_msg
            assert modname is None
