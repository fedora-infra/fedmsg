# Koji callback for sending notifications about events to a messagebus (amqp broker)
# Copyright (c) 2009 Red Hat, Inc.
#
# Authors:
#     Mike Bonnet <mikeb@redhat.com>

from koji.plugin import callbacks, callback, ignore_error
import ConfigParser
import logging
import qpid.messaging
import os
import krbV

MAX_KEY_LENGTH = 255
CONFIG_FILE = '/etc/koji-hub/plugins/messagebus.conf'

config = None
session = None
target = None

def get_sender():
    global config, session, target
    if session and target:
        try:
            return session.sender(target)
        except:
            logging.getLogger('koji.plugin.messagebus').warning('Error getting session, will retry', exc_info=True)
            session = None
            target = None

    config = ConfigParser.SafeConfigParser()
    config.read(CONFIG_FILE)

    if config.getboolean('broker', 'ssl'):
        url = 'amqps://'
    else:
        url = 'amqp://'
    auth = config.get('broker', 'auth')
    if auth == 'PLAIN':
        url += config.get('broker', 'username') + '/'
        url += config.get('broker', 'password') + '@'
    elif auth == 'GSSAPI':
        ccname = 'MEMORY:messagebus'
        os.environ['KRB5CCNAME'] = ccname
        ctx = krbV.default_context()
        ccache = krbV.CCache(name=ccname, context=ctx)
        cprinc = krbV.Principal(name=config.get('broker', 'principal'), context=ctx)
        ccache.init(principal=cprinc)
        keytab = krbV.Keytab(name='FILE:' + config.get('broker', 'keytab'), context=ctx)
        ccache.init_creds_keytab(principal=cprinc, keytab=keytab)
    else:
        raise koji.PluginError, 'unsupported auth type: %s' % auth

    url += config.get('broker', 'host') + ':'
    url += config.get('broker', 'port')

    conn = qpid.messaging.Connection.establish(url,
                                               sasl_mechanisms=config.get('broker', 'auth'),
                                               heartbeat=60)
    sess = conn.session()
    tgt = """%s;
             { create: sender,
               assert: always,
               node: { type: topic,
                       durable: %s,
                       x-declare: { exchange: "%s",
                                    type: %s } } }""" % \
    (config.get('exchange', 'name'), config.getboolean('exchange', 'durable'),
     config.get('exchange', 'name'), config.get('exchange', 'type'))
    sender = sess.sender(tgt)
    session = sess
    target = tgt

    return sender

def _token_append(tokenlist, val):
    # Replace any periods with underscores so we have a deterministic number of tokens
    val = val.replace('.', '_')
    tokenlist.append(val)

def get_message_subject(msgtype, *args, **kws):
    key = [config.get('topic', 'prefix'), msgtype]

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

@callback(*[c for c in callbacks.keys() if c.startswith('post')])
@ignore_error
def send_message(cbtype, *args, **kws):
    global config
    sender = get_sender()
    if cbtype.startswith('post'):
        msgtype = cbtype[4:]
    else:
        msgtype = cbtype[3:]

    data = kws.copy()
    if args:
        data['args'] = list(args)

    exchange_type = config.get('exchange', 'type')
    if exchange_type == 'topic':
        subject = get_message_subject(msgtype, *args, **kws)
        message = qpid.messaging.Message(subject=subject, content=data)
    elif exchange_type == 'headers':
        headers = get_message_headers(msgtype, *args, **kws)
        message = qpid.messaging.Message(properties=headers, content=data)
    else:
        raise koji.PluginError, 'unsupported exchange type: %s' % exchange_type

    sender.send(message, sync=False)
    sender.sync(timeout=60)
    sender.close()
