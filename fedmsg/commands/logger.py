import sys

import fedmsg
import fedmsg.schema
import fedmsg.decorators

def _log_message(args, message):
    fedmsg.send_message(
        topic='logger.%s' % args.topic,
        msg={fedmsg.schema.LOG: message},
        guess_modname=False,
    )

extra_args = [
    (['--relay'], {
        'dest': 'relay',
        'help': "endpoint of the log relay fedmsg-hub to connect to",
        'default': "tcp://127.0.0.1:3002",
    }),
    (['--message'], {
        'dest': 'message',
        'help': "The message to send.",
    }),
    ([], {
        'dest': 'topic',
        'metavar': "TOPIC",
        'help': "org.fedoraproject.logger.TOPIC",
    }),
]

@fedmsg.decorators.command(extra_args=extra_args)
def main(args):
    """ Emit log messages to the FI bus.

    If --message is not specified, this command accepts messages from stdin.
    """

    kw = dict(args._get_kwargs())
    kw['publish_endpoint'] = None  # Override default publishing behavior
    fedmsg.init(**kw)

    if args.message:
        _log_message(args, args.message)
    else:
        line = sys.stdin.readline()
        while line:
            _log_message(args, line.strip())
            line = sys.stdin.readline()
