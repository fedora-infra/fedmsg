import fedmsg
from fedmsg.commands import command
from fedmsg.config import get_fedmsg_config_path

extra_args = [
]


@command(extra_args=extra_args)
def hub(**kw):
    """ Run the fedmsg hub. """

    from moksha.hub.hub import main
    main(config_path=get_fedmsg_config_path())
