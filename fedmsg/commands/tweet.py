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

import twitter as twitter_api
import bitlyapi

import fedmsg
import fedmsg.meta
from fedmsg.commands import BaseCommand


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

        # Boilerplate..
        self.config['publish_endpoint'] = None
        self.config['name'] = 'relay_inbound'
        self.config['mute'] = True

        # Set up fedmsg
        fedmsg.init(**self.config)
        fedmsg.meta.make_processors(**self.config)

        # Set up twitter and statusnet.. multiple accounts if configured
        settings = self.config.get('tweet_endpoints', [])
        apis = [twitter_api.Api(**endpoint) for endpoint in settings]

        # Set up bitly
        settings = self.config['bitly_settings']
        bitly = bitlyapi.BitLy(
            settings['api_user'],
            settings['api_key'],
        )

        # How long to sleep if we spew too fast.
        hibernate_duration = self.config['tweet_hibernate_duration']
        # Sleep a second or two inbetween messages to try and avoid
        # the hibernate
        intermessage_pause = self.config['tweet_intermessage_pause']

        def _post_to_api(api, message):
            try:
                api.PostUpdate(message)
            except Exception as e:
                if 'Too many notices too fast;' in str(e):
                    # Cool our heels then try again.
                    self.log.info("Sleeping for %i" % hibernate_duration)
                    time.sleep(hibernate_duration)
                    _post_to_api(api, message)
                elif 'json decoding' in str(e):
                    # Let it slide ... no idea what this one is.
                    pass
                elif 'duplicate' in str(e):
                    # Let it slide ...
                    pass
                else:
                    raise

        for name, ep, topic, msg in fedmsg.tail_messages(**self.config):
            try:
                message = fedmsg.meta.msg2subtitle(msg, **self.config)
                link = fedmsg.meta.msg2link(msg, **self.config)

                if link:
                    try:
                        link = bitly.shorten(longUrl=link)['url']
                    except Exception:
                        self.log.warn("Bad URI for bitly %r" % link)
                        link = ""

                    message = message[:137 - len(link)] + " " + link
                else:
                    message = message[:139]

                if not message:
                    self.log.info("Not tweeting blank message.")
                    continue

                self.log.info("Tweeting %r" % message)
                for api in apis:
                    _post_to_api(api, message)

                time.sleep(intermessage_pause)
            except Exception as e:
                self.log.error(traceback.format_exc())


def tweet():
    command = TweetCommand()
    command.execute()
