config = dict(
    irc=[
        dict(
            network='irc.freenode.net',
            port=6667,
            nickname='fedmsg-dev',
            channel='fedora-fedmsg',
            make_pretty=True,
            make_terse=True,
            # Don't show the heartbeat... gross.
            filters=dict(
                topic=[],
                body=['lub-dub'],
            ),
        ),
    ],
)
