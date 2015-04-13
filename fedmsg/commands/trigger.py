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

import re
import subprocess
import sys
import threading
from six.moves import queue

import fedmsg
import fedmsg.encoding
from fedmsg.commands import BaseCommand


class TriggerCommand(BaseCommand):
    """ Run a command whenever certain messages arrive.

    Feed the message to the given command over stdin.
    """

    name = "fedmsg-trigger"
    extra_args = [
        (['--topic'], {
            'dest': 'topic',
            'help': 'The topic pattern to listen for.  Everything by default.',
            'default': '',
        }),
        (['--exclude'], {
            'dest': 'exclusive_regexp',
            'metavar': 'REGEXP',
            'help': 'Only show topics that do not match the supplied regexp.',
            'default': '_heartbeat',
        }),
        (['--include'], {
            'dest': 'inclusive_regexp',
            'metavar': 'REGEXP',
            'help': 'Only show topics that match the supplied regexp.',
            'default': '^((?!_heartbeat).)*$',
        }),
        (['--command'], {
            'dest': 'command',
            'metavar': 'COMMAND',
            'help': 'Command to run when a message matches our criteria.',
            'default': None,
        }),
        (['--wait-for'], {
            'dest': 'wait_for',
            'help': 'Seconds to delay after the matching message before ' +
                    'executing command. Timer resets with every matching ' +
                    'message',
            'default': 0,
        }),
        (['--max-queue-size'], {
            'dest': 'max_queue_size',
            'help': 'The max size of the queue before ignoring the delay.',
            'default': 0,
        }),
    ]

    def run_command(self, command, message):
        """ Use subprocess; feed the message to our command over stdin """
        proc = subprocess.Popen([
            'echo \'%s\' | %s' % (fedmsg.encoding.dumps(message), command)
        ], shell=True, executable='/bin/bash')
        return proc.wait()

    def run(self):

        # This is a "required" option... :P
        if not self.config['command']:
            self.log.error("You must provide a --command to run.")
            sys.exit(1)

        # Disable sending
        self.config['publish_endpoint'] = None

        # Disable timeouts.  We want to tail forever!
        self.config['timeout'] = 0

        # Even though fedmsg-trigger won't be sending any messages, give it a
        # name to conform with the other commands.
        self.config['name'] = 'relay_inbound'

        # Tail is never going to send any messages, so we suppress warnings
        # about having no publishing sockets established.
        self.config['mute'] = True

        fedmsg.init(**self.config)

        exclusive_regexp = re.compile(self.config['exclusive_regexp'])
        inclusive_regexp = re.compile(self.config['inclusive_regexp'])

        wait_for = int(self.config['wait_for'])
        max_queue_size = int(self.config['max_queue_size'])

        timer = None
        que = queue.Queue()

        def execute_queue():
            while not que.empty():
                message = que.get()

                result = self.run_command(self.config['command'], message)

                if result != 0:
                    self.log.info("Command returned error code %r" % result)

        try:
            for name, ep, topic, message in fedmsg.tail_messages(**self.config):
                if exclusive_regexp.search(topic):
                    continue

                if not inclusive_regexp.search(topic):
                    continue

                que.put(message)

                if timer is not None:
                    # Try to cancel it
                    timer.cancel()
                if timer is None or not timer.is_alive():
                    # Either there was no timer yet, or it was still waiting
                    # -> Let's start a new one
                    if (max_queue_size > 0 and
                            que.qsize() > max_queue_size):
                        # If the que is too big, let's just run it NOW
                        timer = threading.Timer(0, execute_queue)
                    else:
                        timer = threading.Timer(wait_for,
                                                execute_queue)
                    timer.start()
        except KeyboardInterrupt:
            if timer is not None:
                timer.cancel()
                # Let's wait for commands to finish
                timer.join()


def trigger():
    command = TriggerCommand()
    return command.execute()
