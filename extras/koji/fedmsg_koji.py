# Koji callback for sending notifications about events to the fedmsg messagebus
# Copyright (c) 2009-2012 Red Hat, Inc.
#
# Authors:
#     Ralph Bean <rbean@redhat.com>
#     Mike Bonnet <mikeb@redhat.com>

from koji.plugin import callbacks
from koji.plugin import callback
from koji.plugin import ignore_error

import fedmsg
import kojihub
import re

# Talk to the fedmsg-relay
fedmsg.init(name='relay_inbound', cert_prefix='koji', active=True)

MAX_KEY_LENGTH = 255


def camel_to_dots(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1.\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1.\2', s1).lower()


def get_message_body(topic, *args, **kws):
    msg = {}

    if topic == 'package.list.change':
        msg['tag'] = kws['tag']['name']
        msg['package'] = kws['package']['name']
    elif topic == 'task.state.change':
        msg['method'] = kws['info']['method']
        msg['attribute'] = kws['attribute']
        msg['old'] = kws['old']
        msg['new'] = kws['new']
        msg['owner'] = kojihub.get_user(kws['info']['owner'])['name']
        msg['id'] = kws['info']['id']
    elif topic == 'build.state.change':
        info = kws['info']
        msg['name'] = info['name']
        msg['version'] = info['version']
        msg['release'] = info['release']
        msg['attribute'] = kws['attribute']
        msg['old'] = kws['old']
        msg['new'] = kws['new']
    elif topic == 'import':
        msg['type'] = kws['type']
    elif topic in ('tag', 'untag'):
        msg['tag'] = kws['tag']['name']
        build = kws['build']
        msg['name'] = build['name']
        msg['version'] = build['version']
        msg['release'] = build['release']
        msg['user'] = kws['user']['name']
    elif topic == 'repo.init':
        msg['tag'] = kws['tag']['name']
    elif topic == 'repo.done':
        msg['tag'] = kws['repo']['tag_name']

    return msg


# This callback gets run for every koji event that starts with "post"
@callback(*[c for c in callbacks.keys() if c.startswith('post')])
@ignore_error
def send_message(cbtype, *args, **kws):
    if cbtype.startswith('post'):
        msgtype = cbtype[4:]
    else:
        msgtype = cbtype[3:]

    topic = camel_to_dots(msgtype)
    body = get_message_body(topic, *args, **kws)

    fedmsg.publish(topic=topic, msg=body, modname='koji')
