import unittest

import mock

from fedmsg.consumers import ircbot


class TestIRCConsumer(unittest.TestCase):
    """Tests for the :class:`fedmsg.consumers.ircbot.IRCBotConsumer`."""

    def setUp(self):
        self.hub = mock.Mock()
        self.hub.config = {
            'fedmsg.consumers.ircbot.enabled': True,
            'moksha.blocking_mode': True,
            'topic_prefix_re': 'whatever...',
            'irc_method': 'notice',
            'irc': [
                dict(
                    network='irc.freenode.net',
                    port=6667,
                    ssl=False,
                    nickname='fedmsg-dev',
                    channel='my-fedmsg-channel',
                    timeout=120,
                    make_pretty=True,
                    make_terse=True,
                    make_short=True,
                    line_rate=0.9,
                    filters=dict(),
                ),
            ]
        }

    @mock.patch('fedmsg.consumers.ircbot.IRCBotConsumer.apply_filters')
    @mock.patch('fedmsg.consumers.ircbot.IRCBotConsumer.prettify')
    def test_message_headers(self, prettify, apply_filters):
        """ Assert that headers are copied into the inner message.

        https://github.com/fedora-infra/fedmsg/pull/432
        """
        apply_filters.return_value = True
        consumer = ircbot.IRCBotConsumer(self.hub)
        consumer.irc_clients = [mock.Mock()]
        consumer._consume({'topic': 'testtopic', 'body': {'my': 'msg'}, 'headers': 'awesome'})
        consumer.prettify.assert_called_once_with(
            topic='testtopic',
            msg=dict(topic='testtopic', msg=dict(my='msg'), headers='awesome'),
            pretty=mock.ANY,
            short=mock.ANY,
            terse=mock.ANY,
        )
