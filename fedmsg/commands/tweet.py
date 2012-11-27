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

import twitter as twitter_api
import bitlyapi

import fedmsg
import fedmsg.meta
from fedmsg.commands import command


@command(name="fedmsg-tweet", extra_args=[], daemonizable=True)
def tweet(**kw):
    """ Rebroadcast messages to twitter and statusnet

    New values in the fedmsg configuration are needed for this to work.  Lists
    and dicts of authentication credentials such as:

        - :term:`tweet_endpoints`
        - :term:`bitly_settings`

    And scalars to help with rate limiting such as:

        - :term:`tweet_hibernate_duration`
        - :term:`tweet_intermessage_pause`

    """

    # First, sanity checking.
    if not kw.get('tweet_endpoints', None):
        raise ValueError("Not configured to tweet.")

    # Boilerplate..
    kw['publish_endpoint'] = None
    kw['name'] = 'relay_inbound'
    kw['mute'] = True

    # Set up fedmsg
    fedmsg.init(**kw)
    fedmsg.meta.make_processors(**kw)

    # Set up twitter and statusnet.. multiple accounts if configured
    settings = kw.get('tweet_endpoints', [])
    apis = [twitter_api.Api(**endpoint) for endpoint in settings]

    # Set up bitly
    settings = kw['bitly_settings']
    bitly = bitlyapi.BitLy(
        settings['api_user'],
        settings['api_key'],
    )

    # How long to sleep if we spew too fast.
    hibernate_duration = kw['tweet_hibernate_duration']
    # Sleep a second or two inbetween messages to try and avoid the hibernate
    intermessage_pause = kw['tweet_intermessage_pause']

    def _post_to_api(api, message):
        try:
            api.PostUpdate(message)
        except Exception as e:
            if 'Too many notices too fast;' in str(e):
                # Cool our heels then try again.
                print "Sleeping for", hibernate_duration
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

    for name, ep, topic, msg in fedmsg.tail_messages(**kw):
        message = fedmsg.meta.msg2subtitle(msg, **kw)
        link = fedmsg.meta.msg2link(msg, **kw)

        if link:
            link = bitly.shorten(longUrl=link)['url']
            message = message[:138 - len(link)] + " " + link
        else:
            message = message[:140]

        print("Tweeting %r" % message)
        for api in apis:
            _post_to_api(api, message)

        time.sleep(intermessage_pause)
