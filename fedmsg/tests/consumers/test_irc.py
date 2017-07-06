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

    @mock.patch('fedmsg.meta.msg2link')
    @mock.patch('fedmsg.consumers.ircbot._default_link_shortener')
    def test_default_shortener_is_used(self, shortener, link):
        """ Assert that the default shortener gets called.

        https://github.com/fedora-infra/fedmsg/pull/430
        """
        link.return_value = 'the link'
        consumer = ircbot.IRCBotConsumer(self.hub)
        consumer.prettify(
            topic='testtopic',
            msg=dict(topic='testtopic', msg=dict(my='msg'), headers='awesome'),
            pretty=True, terse=True, short=True)
        shortener.assert_called_once_with('the link')

    @mock.patch('requests.get')
    def test_default_shortener_happy_path(self, get):
        """ Make sure the default shortener happy path works.

        https://github.com/fedora-infra/fedmsg/pull/430
        """
        expected = 'much better'
        get.return_value = mock.Mock()
        get.return_value.text = ' ' + expected + ' '
        result = ircbot._default_link_shortener('some garbage')
        self.assertEqual(result, expected)

    @mock.patch('requests.get')
    def test_default_shortener_failure(self, get):
        """ Make sure the default shortener handles failure.

        https://github.com/fedora-infra/fedmsg/pull/430
        """
        get.side_effect = Exception
        original = 'some garbage'
        result = ircbot._default_link_shortener(original)
        self.assertEqual(result, original)

    @mock.patch('fedmsg.meta.msg2link')
    def test_custom_shortener(self, link):
        """ Assert that a custom shortener gets called.

        https://github.com/fedora-infra/fedmsg/pull/430
        """
        link.return_value = 'the link'
        custom = mock.Mock()

        consumer = ircbot.IRCBotConsumer(self.hub)
        consumer.prettify(
            topic='testtopic',
            msg=dict(topic='testtopic', msg=dict(my='msg'), headers='awesome'),
            pretty=True, terse=True, short=custom)
        custom.assert_called_once_with('the link')
