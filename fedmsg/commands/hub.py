import fedmsg
from fedmsg.commands import command

extra_args = []


@command(extra_args=extra_args)
def hub(**kw):
    """ Run the fedmsg hub. """

    from moksha.hub.hub import main
    main(options=kw)
