import simplejson
import simplejson.encoder

class FedMsgEncoder(simplejson.encoder.JSONEncoder):
    """ Encoder with support for __json__ methods. """

    def default(self, obj):
        if hasattr(obj, '__json__'):
            return obj.__json__()
        return super(FedMsgEncoder, self).default(obj)

encoder = FedMsgEncoder()
dumps = encoder.encode
loads = simplejson.loads

__all__ = [
    'dumps',
    'loads',
]
