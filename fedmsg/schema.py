AGENT = 'agent'     # Generic use.  "Who is responsible for this event?"
USER = 'user'       # FAS
TAG = 'tag'         # For fedora-tagger
LOG = 'log'         # For fedmsg-logger
UPDATE = 'update'   # For bodhi

# Used only for testing and developing.
TEST = 'test'

# Build a list for use in validation
__k, __v = None, None
keys = [__v for __k, __v in globals().items() if not __k.startswith('__')]
