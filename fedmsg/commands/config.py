import fedmsg.config
import fedmsg.json


def config():
    __doc__ = "Simply print out the fedmsg-config as a JSON."
    config = fedmsg.config.load_config([], __doc__)
    print fedmsg.json.pretty_dumps(config)
