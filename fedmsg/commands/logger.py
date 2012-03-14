import argparse
import inspect
import sys

import fedmsg
import fedmsg.schema


def get_calling_docstring(n=1):
    """ Print the docstring of the calling function """
    frame = inspect.stack()[n][0]
    return frame.f_globals[frame.f_code.co_name].__doc__


def process_arguments():
    parser = argparse.ArgumentParser(description=get_calling_docstring(2))
    parser.add_argument(
        '--topic', dest='topic', type=str, metavar="TOPIC",
        help="org.fedoraproject.logger.TOPIC",
        required=True,
    )
    parser.add_argument(
        '--message', dest='message', type=str,
        help="The message to send.",
    )
    parser.add_argument(
        '--relay', dest='relay', type=str,
        help="endpoint of the log relay fedmsg-hub to connect to",
        default="tcp://127.0.0.1:3002",
    )
    args = parser.parse_args()
    return args


def _log_message(args, message):
    fedmsg.send_message(
        topic='logger.%s' % args.topic,
        msg={fedmsg.schema.LOG: message},
        guess_modname=False,
    )


def main():
    """ Emit log messages to the FI bus.

    If --message is not specified, this command accepts messages from stdin.
    """

    args = process_arguments()
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
