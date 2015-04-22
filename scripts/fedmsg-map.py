#!/usr/bin/env python
""" Utility to scan a fedmsg setup for port availability.

Reports what percentage of fedmsg endpoints are bound and ready.
"""

import base64
import collections
import socket
import sys
import time

import fedmsg.config
config = fedmsg.config.load_config()

timeout = 0.2
expected = '/wAAAAAAAAABfw=='

active = collections.defaultdict(list)
inactive = collections.defaultdict(list)

for_collectd = 'verbose' not in sys.argv


def info(content="\n"):
    if not for_collectd:
        sys.stdout.write(content)
        sys.stdout.flush()


def do_scan():
    for i, item in enumerate(config['endpoints'].items()):
        name, endpoints = item
        for endpoint in endpoints:
            if not endpoint.startswith('tcp://'):
                raise ValueError("Don't know how to deal with %r" % endpoint)
            endpoint = endpoint[len('tcp://'):].split(':')
            connection = None
            try:
                connection = socket.create_connection(endpoint, timeout)
                actual = base64.b64encode(connection.recv(10))
                if actual != expected:
                    inactive[name].append((
                        endpoint, "%r is not %r" % (actual, expected)))
                    info("F")
                else:
                    active[name].append((endpoint, "all active"))
                    info(".")
            except socket.error as e:
                inactive[name].append((endpoint, str(e)))
                info("F")
                if connection:
                    connection.close()

    info()

    if 'verbose' in sys.argv:
        import pprint;
        pprint.pprint(dict(active))
        pprint.pprint(dict(inactive))

    header = "".join([
        "name".center(29),
        "active".rjust(8),
        "inactive".rjust(9),
        "percent".rjust(9),
        "reason".center(32),
    ])
    info()
    info(header + "\n")
    info("-" * len(header) + "\n")

    active_n_total, inactive_n_total = 0, 0
    for name in sorted(config['endpoints']):
        active_n = len(active[name])
        inactive_n = len(inactive[name])

        active_n_total += active_n
        inactive_n_total += inactive_n

        total = active_n + inactive_n

        percent = ""
        if total:
            percent = "%%%0.1f" % (100 * float(active_n) / total)

        reasons = set([reason for _, reason in inactive[name]])

        info(name.rjust(29))
        info(str(active_n).rjust(8))
        info(str(inactive_n).rjust(9))
        info(percent.rjust(9))
        info(", ".join(reasons).rjust(32) + "\n")

    info("-" * len(header) + "\n")

    info("  total active:   %i\n" % active_n_total)
    info("total inactive:   %i\n" % inactive_n_total)
    value = 100 * float(active_n_total) / (active_n_total + inactive_n_total)
    info("percent active: %%%0.1f\n" % value)
    return value

if not for_collectd:
    do_scan()
else:
    interval = 10
    host = socket.getfqdn()
    while True:
        start = timestamp = time.time()
        value = do_scan()
        stop = time.time()
        delta = stop - start
        output = (
            "PUTVAL "
            "{host}/fedmsg/percent "
            "interval={interval} "
            "{timestamp}:{value}"
        ).format(
            host=host,
            interval=interval,
            timestamp=int(timestamp),
            value=value)
        print(output)
        if interval - delta > 0:
            time.sleep(interval - delta)
