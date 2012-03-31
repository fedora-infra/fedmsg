AGENT = 'agent'     # Generic use.  "Who is responsible for this event?"
FIELDS = 'fields'   # A list of fields that may be of interest.  For instance,
                    # fas uses this to specify which fields were updated in
                    # a user.update event.

USER = 'user'       # FAS
TAG = 'tag'         # For fedora-tagger
LOG = 'log'         # For fedmsg-logger
UPDATE = 'update'   # For bodhi

# Used only for testing and developing.
TEST = 'test'

# Build a list for use in validation
__k, __v = None, None
keys = [__v for __k, __v in globals().items() if not __k.startswith('__')]
