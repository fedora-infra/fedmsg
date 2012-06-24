import time
import datetime

try:
    # py2.7
    from collections import OrderedDict
except ImportError:
    # py2.4, 2.5, 2.6
    from orderedict import OrderedDict

import simplejson
import simplejson.encoder


class FedMsgEncoder(simplejson.encoder.JSONEncoder):
    """ Encoder with support for __json__ methods. """

    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        if isinstance(obj, datetime.datetime):
            return time.mktime(obj.timetuple())
        return super(FedMsgEncoder, self).default(obj)

encoder = FedMsgEncoder()


def dumps(d):
    """ Encode a dict as JSON.

    Ensure that the keys are ordered so that messages can be signed
    consistently.  See https://github.com/ralphbean/fedmsg/issues/42
    """
    # TODO - Look into using the sort_keys argument to simplejson.  It should
    # introduce less overhead than all this potential dict-copying.
    return encoder.encode(OrderedDict(sorted(d.items())))

pretty_encoder = FedMsgEncoder(indent=2)
pretty_dumps = pretty_encoder.encode

loads = simplejson.loads

__all__ = [
    'pretty_dumps',
    'dumps',
    'loads',
]
