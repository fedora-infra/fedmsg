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

import twitter as twitter_api
import bitlyapi

import fedmsg
import fedmsg.text
from fedmsg.commands import command


@command(name="fedmsg-tweet", extra_args=[], daemonizable=True)
def tweet(**kw):
    """ Rebroadcast messages to twitter """

    # First, sanity checking.
    if not 'tweet_settings' in kw and not 'statusnet_settings' in kw:
        raise ValueError("Not configured to tweet.")

    # Boilerplate..
    kw['publish_endpoint'] = None
    kw['name'] = 'relay_inbound'
    kw['mute'] = True

    # Set up fedmsg
    fedmsg.init(**kw)
    fedmsg.text.make_processors(**kw)

    apis = []
    # Set up twitter if configured
    settings = kw.get('tweet_settings', [])
    if settings:
        apis.append(twitter_api.Api(**settings))

    # Set up statusnet if configured
    settings = kw.get('statusnet_settings', [])
    if settings:
        apis.append(twitter_api.Api(**settings))

    # Set up bitly
    settings = kw['bitly_settings']
    bitly = bitlyapi.BitLy(
        settings['api_user'],
        settings['api_key'],
    )

    for name, ep, topic, message in fedmsg.tail_messages(**kw):
        link = fedmsg.text.msg2link(message, **kw)
        link = bitly.shorten(longUrl=link)['url']
        message = fedmsg.text.msg2subtitle(message, **kw)
        message = (message[:139] + " ")[:139 - len(link)] + link
        print("Tweeting %r" % message)
        for api in apis:
            try:
                api.PostUpdate(message)
            except Exception as e:
                if 'Status is a duplicate' in str(e):
                    # Let it slide ...
                    pass
                else:
                    raise
