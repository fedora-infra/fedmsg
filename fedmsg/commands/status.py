import sys
from fabulous.color import red, green

import fedmsg
from fedmsg.commands import command

def _colorize(success):
    if success:
        return green("  OK  ")
    else:
        return red(" FAIL ")

extra_args = [
    (['--producers'], {
        'dest': 'endpoints',
        'help': 'The list of producers to check',
        'metavar': 'endpoint',
        'nargs': '*',
        'default': ["tcp://127.0.0.1:6543"],
    }),
]

@command(extra_args=extra_args)
def status(**kwargs):
    """ Check the status of nodes on the bus. """

    # Disable sending
    kwargs['publish_endpoint'] = None
    fedmsg.init(**kwargs)

    status = fedmsg.have_pulses(**kwargs)

    for endpoint, success in status.iteritems():
        print "[%s]  %s" % (_colorize(success), endpoint)
