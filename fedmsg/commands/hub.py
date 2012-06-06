import fedmsg
from fedmsg.commands import command

extra_args = [
    (['--websocket-server-port'], {
        'dest': 'moksha.livesocket.websocket.port',
        'type': int,
        'help': 'Port on which to host the websocket server.',
        'default': None,
    }),
]


@command(extra_args=extra_args)
def hub(**kw):
    """ Run the fedmsg hub. """

    # Check if the user wants the websocket server to run
    if kw['moksha.livesocket.websocket.port']:
        kw['moksha.livesocket.backend'] = 'websocket'

    # Rephrase the fedmsg-config.py config as moksha *.ini format.
    # Note that the hub we kick off here cannot send any message.  You should
    # use fedmsg.send_message(...) still for that.
    moksha_options = dict(
        zmq_subscribe_endpoints=','.join(
            ','.join(bunch) for bunch in kw['endpoints'].values()
        ),
    )
    kw.update(moksha_options)

    from moksha.hub import main
    main(options=kw)
