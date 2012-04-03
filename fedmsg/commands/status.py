import sys
from fabulous.color import red, green

import fedmsg
from fedmsg.commands import command


def _colorize(success):
    if success:
        return green("  OK  ")
    else:
        return red(" FAIL ")

extra_args = []


@command(extra_args=extra_args)
def status(**kwargs):
    """ Check the status of nodes on the bus. """

    # Disable sending
    fedmsg.init(**kwargs)

    status = fedmsg.have_pulses(**kwargs)

    for endpoint, success in status.iteritems():
        print "[%s]  %s" % (_colorize(success), endpoint)
