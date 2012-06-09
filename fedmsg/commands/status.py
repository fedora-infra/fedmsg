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


@command(name="fedmsg-status", extra_args=extra_args)
def status(**kwargs):
    """ Check the status of fedmsg-hub instances.

    This command is a work in progress.  For the moment, it returns results for
    every endpoint listed in `fedmsg-config`, but not every endpoint is
    associated with a hub.  Many are associated with WSGI processes which have
    no fedmsg heartbeat.  Lots of false alarms will be reported until this is
    resolved.
    """

    # Disable sending
    fedmsg.init(**kwargs)

    status = fedmsg.have_pulses(**kwargs)

    padding = max(map(len, kwargs['endpoints']))
    for name, endpoint, success in fedmsg.have_pulses(**kwargs):
        print "[%s]  %s %s" % (
            _colorize(success),
            name.rjust(padding),
            endpoint,
        )
