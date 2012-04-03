import sys

import fedmsg
import fedmsg.json
from fedmsg.commands import command


def _log_message(kw, message):
    msg = {'log': message}
    if kw['json_input']:
        msg = fedmsg.json.loads(message)

    fedmsg.send_message(
        topic=kw['topic'],
        msg=msg,
        modname=kw['modname'],
    )

extra_args = [
    (['--message'], {
        'dest': 'message',
        'help': "The message to send.",
    }),
    (['--json-input'], {
        'dest': 'json_input',
        'action': 'store_true',
        'default': False,
        'help': "Take each line of input as JSON.",
    }),
    (['--topic'], {
        'dest': 'topic',
        'metavar': "TOPIC",
        'default': "log",
        'help': "Think org.fedoraproject.logger.TOPIC",
    }),
    (['--modname'], {
        'dest': 'modname',
        'metavar': "MODNAME",
        'default': "logger",
        'help': "More control over the topic.  Think org.fp.MODNAME.TOPIC.",
    }),
]


@command(extra_args=extra_args)
def logger(**kwargs):
    """ Emit log messages to the FI bus.

    If --message is not specified, this command accepts messages from stdin.
    """

    kwargs['active'] = True
    kwargs['endpoints']['relay_inbound'] = kwargs['relay_inbound']
    fedmsg.init(name='relay_inbound', **kwargs)

    if kwargs.get('message', None):
        _log_message(kwargs, kwargs['message'])
    else:
        line = sys.stdin.readline()
        while line:
            _log_message(kwargs, line.strip())
            line = sys.stdin.readline()
