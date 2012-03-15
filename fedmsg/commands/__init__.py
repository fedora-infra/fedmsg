import fedmsg.config


class command(object):
    """ Convenience decorator for wrapping fedmsg console script commands.

    Accepts a list of extra args.  See fedmsg.commands.logger for an example.
    """

    def __init__(self, extra_args=None):
        self.extra_args = extra_args or []

    def __call__(self, func):

        def wrapper():
            args = fedmsg.config.process_arguments(self.extra_args)
            kwargs = dict(args._get_kwargs())
            return func(**kwargs)

        # TODO -- this doesn't work.
        wrapper.__doc__ = func.__doc__

        return wrapper
