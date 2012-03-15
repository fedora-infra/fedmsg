import fedmsg.config

class command(object):
    def __init__(self, extra_args):
        self.extra_args = extra_args or []

    def __call__(self, func):

        def wrapper():
            args = fedmsg.config.process_arguments(self.extra_args)
            return func(args)

        # TODO -- this doesn't work.
        wrapper.__doc__ = func.__doc__

        return wrapper
