import fedmsg
from fedmsg.commands import command

extra_args = []


@command(extra_args=extra_args)
def hub(**kw):
    """ Run the fedmsg hub. """

    # Rephrase the fedmsg-config.py config as moksha *.ini format.
    # Note that the hub we kick off here cannot send any message.  You should
    # use fedmsg.send_message(...) still for that.
    moksha_options = dict(
        zmq_enabled=True,
        zmq_subscribe_endpoints=','.join(kw['endpoints'].values()),
        zmq_strict=True,
    )
    kw.update(moksha_options)

    from moksha.hub import main
    main(options=kw)
