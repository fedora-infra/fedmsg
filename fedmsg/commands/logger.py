import sys

import fedmsg
import fedmsg.json
from fedmsg.commands import command


def _log_message(kw, message):
    msg = {'log': message}
    if kw['json_input']:
        msg = fedmsg.json.loads(message)

    fedmsg.publish(
        topic=kw['topic'],
        msg=msg,
        modname=kw['modname'],
    )

extra_args = [
    (['--message'], {
        'dest': 'logger_message',
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


@command(name="fedmsg-logger", extra_args=extra_args)
def logger(**kwargs):
    """
    Emit log messages to the FI bus.

    If the fedmsg-relay service is not running at the address specified in
    fedmsg-config.py, then this command will *hang* until that service becomes
    available.

    If --message is not specified, this command accepts messages from stdin.

    Some examples::

        $ echo '{"a": 1}' | fedmsg-logger --json-input
        $ echo "Hai there." | fedmsg-logger --modname=git --topic=repo.update
        $ fedmsg-logger --message="This is a message."
        $ fedmsg-logger --message='{"a": 1}' --json-input

    """

    kwargs['active'] = True
    kwargs['endpoints']['relay_inbound'] = kwargs['relay_inbound']
    fedmsg.init(name='relay_inbound', **kwargs)

    if kwargs.get('logger_message'):
        _log_message(kwargs, kwargs.get('logger_message'))
    else:
        line = sys.stdin.readline()
        while line:
            _log_message(kwargs, line.strip())
            line = sys.stdin.readline()
