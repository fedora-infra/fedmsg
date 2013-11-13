import unittest
import fedmsg.encoding

from nose.tools import eq_


class TestEncoding(unittest.TestCase):
    def test_float_precision(self):
        """ Ensure that float precision is limited to 3 decimal places. """
        msg = dict(some_number=1234.123456)
        json_str = fedmsg.encoding.dumps(msg)
        print json_str
        output = fedmsg.encoding.loads(json_str)
        eq_(str(output['some_number']), '1234.123')
