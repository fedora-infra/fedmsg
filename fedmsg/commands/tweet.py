# This file is part of fedmsg.
# Copyright (C) 2012 Red Hat, Inc.
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
#

import time
import traceback

import fedmsg
import fedmsg.meta
from fedmsg.commands import BaseCommand
from fedmsg.consumers.tweet import TweetBotConsumer


class TweetCommand(BaseCommand):
    """ Rebroadcast messages to twitter and statusnet

    New values in the fedmsg configuration are needed for this to work.  Lists
    and dicts of authentication credentials such as:

        - :term:`tweet_endpoints`
        - :term:`bitly_settings`

    And scalars to help with rate limiting such as:

        - :term:`tweet_hibernate_duration`
        - :term:`tweet_intermessage_pause`

    """
    name = "fedmsg-tweet"
    extra_args = []
    daemonizable = True

    def run(self):
        # First, sanity checking.
        if not self.config.get('tweet_endpoints', None):
            raise ValueError("Not configured to tweet.")

        # Do just like in fedmsg.commands.hub and mangle fedmsg-config.py to
        # work with moksha's expected configuration.
        moksha_options = dict(
            zmq_subscribe_endpoints=','.join(
                ','.join(bunch) for bunch in self.config['endpoints'].values()
            ),
        )
        self.config.update(moksha_options)
        self.config[TweetBotConsumer.config_key] = True

        from moksha.hub import main
        main(
            # Pass in our config dict
            options=self.config,
            # Only run this *one* consumer
            consumers=[TweetBotConsumer],
            # Tell moksha to quiet its logging.
            framework=False,
        )


def tweet():
    command = TweetCommand()
    command.execute()
