# Koji callback for sending notifications about events to the fedmsg messagebus
# Copyright (c) 2009-2012 Red Hat, Inc.
#
# Authors:
#     Mike Bonnet <mikeb@redhat.com>
#     Ralph Bean <rbean@redhat.com>

from koji.plugin import callbacks, callback, ignore_error

MAX_KEY_LENGTH = 255


def _token_append(tokenlist, val):
    # Replace any periods with underscores so we have a
    # deterministic number of tokens
    val = val.replace('.', '_')
    tokenlist.append(val)


def get_message_subject(msgtype, *args, **kws):
    key = [msgtype]

    if msgtype == 'PackageListChange':
        _token_append(key, kws['tag']['name'])
        _token_append(key, kws['package']['name'])
    elif msgtype == 'TaskStateChange':
        _token_append(key, kws['info']['method'])
        _token_append(key, kws['attribute'])
    elif msgtype == 'BuildStateChange':
        info = kws['info']
        _token_append(key, kws['attribute'])
        _token_append(key, info['name'])
    elif msgtype == 'Import':
        _token_append(key, kws['type'])
    elif msgtype in ('Tag', 'Untag'):
        _token_append(key, kws['tag']['name'])
        build = kws['build']
        _token_append(key, build['name'])
        _token_append(key, kws['user']['name'])
    elif msgtype == 'RepoInit':
        _token_append(key, kws['tag']['name'])
    elif msgtype == 'RepoDone':
        _token_append(key, kws['repo']['tag_name'])

    key = '.'.join(key)
    key = key[:MAX_KEY_LENGTH]
    return key


def get_message_headers(msgtype, *args, **kws):
    headers = {'type': msgtype}

    if msgtype == 'PackageListChange':
        headers['tag'] = kws['tag']['name']
        headers['package'] = kws['package']['name']
    elif msgtype == 'TaskStateChange':
        headers['method'] = kws['info']['method']
        headers['attribute'] = kws['attribute']
        headers['old'] = kws['old']
        headers['new'] = kws['new']
    elif msgtype == 'BuildStateChange':
        info = kws['info']
        headers['name'] = info['name']
        headers['version'] = info['version']
        headers['release'] = info['release']
        headers['attribute'] = kws['attribute']
        headers['old'] = kws['old']
        headers['new'] = kws['new']
    elif msgtype == 'Import':
        headers['importType'] = kws['type']
    elif msgtype in ('Tag', 'Untag'):
        headers['tag'] = kws['tag']['name']
        build = kws['build']
        headers['name'] = build['name']
        headers['version'] = build['version']
        headers['release'] = build['release']
        headers['user'] = kws['user']['name']
    elif msgtype == 'RepoInit':
        headers['tag'] = kws['tag']['name']
    elif msgtype == 'RepoDone':
        headers['tag'] = kws['repo']['tag_name']

    return headers


# This callback gets run for every koji event that starts with "post"
@callback(*[c for c in callbacks.keys() if c.startswith('post')])
@ignore_error
def send_message(cbtype, *args, **kws):
    if cbtype.startswith('post'):
        msgtype = cbtype[4:]
    else:
        msgtype = cbtype[3:]

    data = kws.copy()
    if args:
        data['args'] = list(args)

    fedmsg.publish(
        topic=get_message_subject(msgtype, *args, **kws),
        msg=data,
        modname='koji',
    )
