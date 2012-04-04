import fedmsg
from fedmsg.commands import command

extra_args = [
    ([], {
        'dest': 'name',
        'metavar': "NAME",
        'help': "Name of the publishing endpoint to use.",
    }),
]


@command(extra_args=extra_args)
def hub(**kw):
    """ Run the fedmsg hub. """

    if kw['name'] not in kw['endpoints']:
        raise ValueError("NAME must be one of %r" % kw['endpoints'].keys())

    # Rephrase the fedmsg-config.py config as moksha *.ini format.
    moksha_options = dict(
        zmq_enabled=True,
        zmq_publish_endpoints=kw['endpoints'][kw['name']],
        zmq_subscribe_endpoints=','.join(kw['endpoints'].values()),
        zmq_strict=True,
    )
    kw.update(moksha_options)

    from moksha.hub import main
    main(options=kw)
