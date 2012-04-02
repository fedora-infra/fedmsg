__schema = dict(
    AGENT = 'agent',     # Generic use.  "Who is responsible for this event?"
    FIELDS = 'fields',   # A list of fields that may be of interest.  For instance,
                         # fas uses this to specify which fields were updated in
                         # a user.update event.

    USER = 'user',       # FAS
    GROUP = 'group',     # FAS

    TAG = 'tag',         # For fedora-tagger
    LOG = 'log',         # For fedmsg-logger
    UPDATE = 'update',   # For bodhi

    # Used only for testing and developing.
    TEST = 'test',
)

# Add these to the toplevel for backwards compat
for __i in __schema:
    vars()[__i] = __schema[__i]

# Build a set for use in validation
### TODO: Consider renaming this as it's not really the "keys" here
keys = frozenset(__schema.values())
