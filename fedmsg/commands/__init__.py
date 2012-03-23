import fedmsg
import fedmsg.config


class command(object):
    """ Convenience decorator for wrapping fedmsg console script commands.

    Accepts a list of extra args.  See fedmsg.commands.logger for an example.
    """

    def __init__(self, extra_args=None):
        self.extra_args = extra_args or []

    def __call__(self, func):

        def wrapper():
            config = fedmsg.config.load_config(
                self.extra_args,
                func.__doc__,
                fedmsg_command=True,
            )
            return func(**config)

        return wrapper
