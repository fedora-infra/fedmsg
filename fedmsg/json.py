import time
import datetime

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
dumps = encoder.encode

pretty_encoder = FedMsgEncoder(indent=2)
pretty_dumps = pretty_encoder.encode

loads = simplejson.loads

__all__ = [
    'pretty_dumps',
    'dumps',
    'loads',
]
