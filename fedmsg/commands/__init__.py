# This file is part of fedmsg.
# Copyright (C) 2014 Red Hat, Inc.
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
import six
import sys

import logging
try:
    # Python2.7 and later
    from logging.config import dictConfig
except ImportError:
    # For Python2.6, we rely on a third party module.
    from logutils.dictconfig import dictConfig


class BaseCommand(object):
    daemonizable = False
    extra_args = None

    def __init__(self):
        if not self.extra_args:
            self.extra_args = []

        if self.daemonizable:
            self.extra_args.append(
                (['--daemon'], {
                    'dest': 'daemon',
                    'help': 'Run in the background as a daemon.',
                    'action': 'store_true',
                    'default': False,
                })
            )

        self.config = self.get_config()
        dictConfig(self.config.get('logging', {'version': 1}))
        self.log = logging.getLogger("fedmsg")

    def get_config(self):
        return fedmsg.config.load_config(
            self.extra_args,
            self.__doc__,
            fedmsg_command=True,
        )

    def _handle_signal(self, signum, stackframe):
        from moksha.hub.reactor import reactor
        from moksha.hub import hub
        from twisted.internet.error import ReactorNotRunning

        if hub._hub:
            hub._hub.stop()

        try:
            reactor.stop()
        except ReactorNotRunning as e:
            warnings.warn(six.text_type(e))

    def _daemonize(self):
        import psutil
        from daemon import DaemonContext
        try:
            from daemon.pidfile import TimeoutPIDLockFile as PIDLockFile
        except:
            from daemon.pidlockfile import PIDLockFile

        pidlock = PIDLockFile('/var/run/fedmsg/%s.pid' % self.name)

        pid = pidlock.read_pid()
        if pid and not psutil.pid_exists(pid):
            self.log.warn("PID file exists but with no proc:  coup d'etat!")
            pidlock.break_lock()

        output = file('/var/log/fedmsg/%s.log' % self.name, 'a')
        daemon = DaemonContext(pidfile=pidlock, stdout=output, stderr=output)
        daemon.terminate = self._handle_signal

        with daemon:
            return self.run()

    def execute(self):
        if self.daemonizable and self.config['daemon'] is True:
            return self._daemonize()
        else:
            try:
                return self.run()
            except KeyboardInterrupt:
                print()
