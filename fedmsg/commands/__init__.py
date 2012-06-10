import fedmsg
import fedmsg.config
import warnings


class command(object):
    """ Convenience decorator for wrapping fedmsg console script commands.

    Accepts a list of extra args.  See fedmsg.commands.logger for an example.
    """

    def __init__(self, name, extra_args=None, daemonizable=False):
        if daemonizable:
            extra_args.append(
                (['--daemon'], {
                    'dest': 'daemon',
                    'help': 'Run in the background as a daemon.',
                    'action': 'store_true',
                    'default': False,
                })
            )

        self.name = name
        self.extra_args = extra_args or []
        self.daemonizable = daemonizable

    def _handle_signal(self, signum, stackframe):
        from moksha.hub.reactor import reactor
        from moksha.hub import hub
        from twisted.internet.error import ReactorNotRunning
        import signal  # TODO -- is this import necessary?

        if hub._hub:
            hub._hub.stop()

        try:
            reactor.stop()
        except ReactorNotRunning, e:
            warnings.warn(str(e))

    def _daemonize(self, func, config):
        from daemon import DaemonContext
        try:
            from daemon.pidfile import TimeoutPIDLockFile as PIDLockFile
        except:
            from daemon.pidlockfile import PIDLockFile

        pidlock = PIDLockFile('/var/run/fedmsg/%s.pid' % self.name)
        output = file('/var/log/fedmsg/%s.log' % self.name, 'a')
        daemon = DaemonContext(pidfile=pidlock, stdout=output, stderr=output)
        daemon.terminate = self._handle_signal

        with daemon:
            return func(**config)

    def __call__(self, func):

        def wrapper():
            config = fedmsg.config.load_config(
                self.extra_args,
                func.__doc__,
                fedmsg_command=True,
            )

            _func = lambda: func(**config)

            if self.daemonizable and config['daemon'] is True:
                return self._daemonize(func, config)
            else:
                return func(**config)

        return wrapper
