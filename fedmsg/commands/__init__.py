# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Ralph Bean <rbean@redhat.com>
#
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

            if self.daemonizable and config['daemon'] is True:
                return self._daemonize(func, config)
            else:
                try:
                    return func(**config)
                except KeyboardInterrupt:
                    print

        # Attach the --help message as the doc string.
        parser = fedmsg.config.build_parser(
            self.extra_args,
            func.__doc__,
            prog=self.name,
        )
        wrapper.__doc__ = parser.format_help()

        return wrapper
