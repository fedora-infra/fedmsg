import sys

import fedmsg
import fedmsg.schema
from fedmsg.commands import command


def _log_message(kw, message):
    fedmsg.send_message(
        topic=kw['topic'],
        msg={fedmsg.schema.LOG: message},
        modname='logger',
    )

extra_args = [
    (['--relay'], {
        'dest': 'relay',
        'help': "Endpoint of the log relay fedmsg-hub to connect to",
        'default': "tcp://127.0.0.1:3002",
    }),
    (['--message'], {
        'dest': 'message',
        'help': "The message to send.",
    }),
    ([], {
        'dest': 'topic',
        'metavar': "TOPIC",
        'help': "Think org.fedoraproject.logger.TOPIC",
    }),
]


@command(extra_args=extra_args)
def logger(**kwargs):
    """ Emit log messages to the FI bus.

    If --message is not specified, this command accepts messages from stdin.
    """

    # Override default publishing behavior
    kwargs['publish_endpoint'] = None
    fedmsg.init(**kwargs)

    if kwargs.get('message', None):
        _log_message(kwargs, kwargs['message'])
    else:
        line = sys.stdin.readline()
        while line:
            _log_message(kwargs, line.strip())
            line = sys.stdin.readline()
