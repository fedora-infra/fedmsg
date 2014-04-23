# This file is part of fedmsg.
# Copyright (C) 2012 - 2014 Red Hat, Inc.
# Copyright (C) 2014 Nicolas Dandrimont <olasd@debian.org>
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
#           Nicolas Dandrimont <olasd@debian.org>
#
from __future__ import print_function

import argparse
import six
import sys
import textwrap

import fedmsg.config
import fedmsg.encoding


def config():
    __doc__ = """
    Query or print the parsed fedmsg-config.

    fedmsg-config is a simple utility that prints out the contents of
    the fully parsed fedmsg config as a JSON dictionary.

    The tool allows you to query a specific configuration key with the
    --query option. It returns an error code of 1 if the key isn't
    found.

    In query mode, the configuration key has the following syntax:
    foo.bar.baz retrieves the value of config["foo"]["bar"]["baz"]

    If the configuration value is an atomic value, it is printed
    directly. If the value is a list, each item gets printed line by
    line. Else, the value is printed as a JSON dictionary.
    """

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog=sys.argv[0],
    )

    parser.add_argument(
        '--config-filename',
        dest='config_filename',
        help="Config file to use.",
        default=None,
    )

    parser.add_argument(
        '--disable-defaults',
        dest='disable_defaults',
        help="Disable the configuration defaults.",
        action="store_true",
    )

    parser.add_argument(
        '--query',
        dest='query',
        help="The key to dump from the given config.",
        type=str,
        default=None
    )

    args = parser.parse_args()

    filenames = None
    if args.config_filename:
        filenames = [args.config_filename]

    config = fedmsg.config.load_config(
        extra_args=[],
        doc=__doc__,
        filenames=filenames,
        disable_defaults=args.disable_defaults,
    )

    cur = config

    if args.query:
        cur = fedmsg.utils.dict_query(cur, args.query)[args.query]
        if cur is None:
            print ("Key `%s` does not exist in config" % args.query,
                   file=sys.stderr)
            sys.exit(1)

    if isinstance(cur, list):
        for i in cur:
            print(i)
    elif isinstance(cur, six.string_types):
        print(cur)
    else:
        print(fedmsg.encoding.pretty_dumps(cur))
