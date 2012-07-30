import fedmsg.config
import fedmsg.encoding


def config():
    __doc__ = "Simply print out the fedmsg-config as a JSON."
    config = fedmsg.config.load_config([], __doc__)
    print fedmsg.encoding.pretty_dumps(config)
