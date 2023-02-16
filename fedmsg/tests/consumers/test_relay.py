import os
import unittest

import mock

from fedmsg.consumers import relay


class TestSigningRelayConsumer(unittest.TestCase):
    """Tests for the :class:`fedmsg.consumers.relays.SigningRelayConsumer`."""

    def setUp(self):
        self.hub = mock.Mock()
        self.signing_cert = (
            u'LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUVYakNDQThlZ0F3SUJBZ0lCR'
            u'HpBTkJna3Fo\na2lHOXcwQkFRc0ZBRENCb0RFTE1Ba0dBMVVFQmhNQ1ZWTXgKQ3pB'
            u'SkJnTlZCQWdUQWs1RE1SQXdE\nZ1lEVlFRSEV3ZFNZV3hsYVdkb01SY3dGUVlEVlF'
            u'RS0V3NUdaV1J2Y21FZwpVSEp2YW1WamRERVBN\nQTBHQTFVRUN4TUdabVZrYlhObk'
            u'1ROHdEUVlEVlFRREV3Wm1aV1J0YzJjeER6QU5CZ05WCkJDa1RC\nbVpsWkcxelp6R'
            u'W1NQ1FHQ1NxR1NJYjNEUUVKQVJZWFlXUnRhVzVBWm1Wa2IzSmhjSEp2YW1WamRD\n'
            u'NXYKY21jd0hoY05Nak13TWpJd01URTBNekV5V2hjTk16TXdNakUzTVRFME16RXlXa'
            u'kNCNGpFTE1B\na0dBMVVFQmhNQwpWVk14Q3pBSkJnTlZCQWdUQWs1RE1SQXdEZ1lE'
            u'VlFRSEV3ZFNZV3hsYVdkb01S\nY3dGUVlEVlFRS0V3NUdaV1J2CmNtRWdVSEp2YW1'
            u'WamRERVBNQTBHQTFVRUN4TUdabVZrYlhObk1U\nQXdMZ1lEVlFRREV5ZHphR1ZzYk'
            u'Mxd1lXTnIKWVdkbGN6QXhMbkJvZURJdVptVmtiM0poY0hKdmFt\nVmpkQzV2Y21je'
            u'E1EQXVCZ05WQkNrVEozTm9aV3hzTFhCaApZMnRoWjJWek1ERXVjR2g0TWk1bVpX\n'
            u'UnZjbUZ3Y205cVpXTjBMbTl5WnpFbU1DUUdDU3FHU0liM0RRRUpBUllYCllXUnRhV'
            u'zVBWm1Wa2Iz\nSmhjSEp2YW1WamRDNXZjbWN3Z1o4d0RRWUpLb1pJaHZjTkFRRUJC'
            u'UUFEZ1kwQU1JR0oKQW9HQkFL\nWUhDV1VhaWo4YlFub25ZVVYwOEdnWWYvWnRSRlB'
            u'IVG9vYnkzQ3Z0Tk5Nc2JETkxnZEhxRUU2WHFs\nSApXM3FWaDNFaktJRHZDdmtzOU'
            u't0endRY0pXZVdXLy9qMVozR1ZZMzZ1WS9vUDAvMEl0dmtaRTZZ\ndHkxNFZ5clI5C'
            u'nZmL3NIVlllTFc2N2FIdW0xYVc3VElMZWxHVE1VUDJQWnNPdk0vNjlLNWpEMzhv\n'
            u'RkFnTUJBQUdqZ2dGaU1JSUIKWGpBSkJnTlZIUk1FQWpBQU1DMEdDV0NHU0FHRytFS'
            u'UJEUVFnRmg1\nRllYTjVMVkpUUVNCSFpXNWxjbUYwWldRZwpRMlZ5ZEdsbWFXTmhk'
            u'R1V3SFFZRFZSME9CQllFRkFz\nZWpLMG9SanVuOWREL0pCZHlZRzJ2VmRJZk1JSGd'
            u'CZ05WCkhTTUVnZGd3Z2RXQUZJVTdDN1dHSWpM\nZHZmamhmSW5ESUszS1JMVTRvWU'
            u'dtcElHak1JR2dNUXN3Q1FZRFZRUUcKRXdKVlV6RUxNQWtHQTFV\nRUNCTUNUa014R'
            u'URBT0JnTlZCQWNUQjFKaGJHVnBaMmd4RnpBVkJnTlZCQW9URGtabApaRzl5WVNC\n'
            u'UWNtOXFaV04wTVE4d0RRWURWUVFMRXdabVpXUnRjMmN4RHpBTkJnTlZCQU1UQm1ab'
            u'FpHMXpaekVQ\nCk1BMEdBMVVFS1JNR1ptVmtiWE5uTVNZd0pBWUpLb1pJaHZjTkFR'
            u'a0JGaGRoWkcxcGJrQm1aV1J2\nY21Gd2NtOXEKWldOMExtOXlaNElVTVJoZm1seSt'
            u'4bVFlL1NDek43S3lGdnZnd1BZd0V3WURWUjBs\nQkF3d0NnWUlLd1lCQlFVSApBd0'
            u'l3Q3dZRFZSMFBCQVFEQWdlQU1BMEdDU3FHU0liM0RRRUJDd1VB\nQTRHQkFGVkVEa'
            u'U93U2k2aWxEMTRiRCtZCmxjT3Rxc0FLY1o2cEpzalRiYVlacDdFRVpUd1NhZEJs\n'
            u'cmtrZThTRkZzQUtnKzREVXU3ejF2Q0NVSHhSeEI1Z0oKYytNM1lrdW9OQXlOZThHY'
            u'VZBbGNBSHo5\ndm95TW05cWhSbHlFa2pIaWNYcWRsK00wOXJlYmJBK1YyNVcyYzk0'
            u'aApETXA1ZWUvalRFSkI3eEpj\nNjdNNW5KbWkKLS0tLS1FTkQgQ0VSVElGSUNBVEU'
            u'tLS0tLQo=\n'
        )
        self.hub.config = {
            'fedmsg.consumers.relay.enabled': True,
            'validate_signatures': False,
            'ssldir': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'test_certs/keys'),
        }

    @mock.patch('fedmsg.consumers.relay.log')
    def test_initialization(self, mock_log):
        """Assert that when the certnames dictionary is mis-configured an error is logged."""
        relay.SigningRelayConsumer(self.hub)
        mock_log.error.assert_called_once_with(
            'The signing relay requires that the certificate name is in '
            'the "certnames" dictionary using the "signing_relay" key')

    def test_message_signed(self):
        """Assert messages are signed prior to relay."""
        self.hub.config['certnames'] = {
            'signing_relay': 'shell-packages01.phx2.fedoraproject.org',
        }
        expected_msg = {
            'my': 'msg',
            'crypto': 'x509',
            'signature': (
                u'cM41fBCf5vWoYQvI9mlVofIJZ/djKXAk+4s8EltzSeW+xWCqJ/EnCTHj'
                u'ZcNGY09CeJRoDcq0Yc1y\nc8QR6IT7JCSlwkc1Iqj+5SKE/REm6AN5Xd'
                u'3jqJHZSWMqKqhxvlzwaWEFI1nNp3qhxWDJNmUKEqIU\nUwl+6CntIulR'
                u'f/5fiO8=\n'
            ),
            'certificate': self.signing_cert,
        }
        consumer = relay.SigningRelayConsumer(self.hub)
        consumer.consume({'topic': 'testtopic', 'body': {'my': 'msg'}})
        self.hub.send_message.assert_called_once_with(topic='testtopic', message=expected_msg)
