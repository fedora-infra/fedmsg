import logging
import os
import requests
import time


_log = logging.getLogger(__name__)


def fix_datagrepper_message(message):
    """
    See if a message is (probably) a datagrepper message and attempt to mutate
    it to pass signature validation.

    Datagrepper adds the 'source_name' and 'source_version' keys. If messages happen
    to use those keys, they will fail message validation. Additionally, a 'headers'
    dictionary is present on all responses, regardless of whether it was in the
    original message or not. This is deleted if it's null, which won't be correct in
    all cases. Finally, datagrepper turns the 'timestamp' field into a float, but it
    might have been an integer when the message was signed.

    A copy of the dictionary is made and returned if altering the message is necessary.

    I'm so sorry.

    Args:
        message (dict): A message to clean up.

    Returns:
        dict: A copy of the provided message, with the datagrepper-related keys removed
            if they were present.
    """
    if not ('source_name' in message and 'source_version' in message):
        return message

    # Don't mutate the original message
    message = message.copy()

    del message['source_name']
    del message['source_version']
    # datanommer adds the headers field to the message in all cases.
    # This is a huge problem because if the signature was generated with a 'headers'
    # key set and we delete it here, messages will fail validation, but if we don't
    # messages will fail validation if they didn't have a 'headers' key set.
    #
    # There's no way to know whether or not the headers field was part of the signed
    # message or not. Generally, the problem is datanommer is mutating messages.
    if 'headers' in message and not message['headers']:
        del message['headers']
    if 'timestamp' in message:
        message['timestamp'] = int(message['timestamp'])

    return message


def validate_policy(topic, signer, routing_policy, nitpicky=False):
    """
    Checks that the sender is allowed to emit messages for the given topic.

    Args:
        topic (str): The message topic the ``signer`` used when sending the message.
        signer (str): The Common Name of the certificate used to sign the message.

    Returns:
        bool: True if the policy defined in the settings allows the signer to send
            messages on ``topic``.
    """
    if topic in routing_policy:
        # If so.. is the signer one of those permitted senders?
        if signer in routing_policy[topic]:
            # We are good.  The signer of this message is explicitly
            # whitelisted to send on this topic in our config policy.
            return True
        else:
            # We have a policy for this topic and $homeboy isn't on the list.
            _log.error("Authorization/routing_policy error.  "
                       "Topic %r.  Signer %r." % (topic, signer))
            return False
    else:
        # We don't have a policy for this topic.  How we react next for an
        # underspecified routing_policy is based on a configuration option.

        # Ideally, we are in nitpicky mode.  We leave it disabled while
        # standing up fedmsg across our environment so that we can build our
        # policy without having the whole thing come crashing down.
        if nitpicky:
            # We *are* in nitpicky mode.  We don't have an entry in the
            # routing_policy for the topic of this message.. and *nobody*
            # gets in without a pass.  That means that we fail the message.
            _log.error("Authorization/routing_policy underspecified.")
            return False
        else:
            # We are *not* in nitpicky mode.  We don't have an entry in the
            # routing_policy for the topic of this message.. but we don't
            # really care.
            _log.warning('No routing policy defined for "{t}" but routing_nitpicky is '
                         'False so the message is being treated as authorized.'.format(t=topic))
            return True


def _load_remote_cert(location, cache, cache_expiry, tries=3, **config):
    """Get a fresh copy from fp.o/fedmsg/crl.pem if ours is getting stale.

    Return the local filename.

    .. note:: This is not a public API and is subject to change.

    Args:
        location (str): The URL where the certificate is hosted.
        cache (str): The absolute path where the certificate should be stored.
        cache_expiry (int): How long the cache should be considered fresh, in seconds.
        tries (int): The number of times to attempt to retry downloading the certificate.

    """
    alternative_cache = os.path.expanduser("~/.local" + cache)

    try:
        modtime = os.stat(cache).st_mtime
    except OSError:
        # File does not exist yet.
        try:
            # Try alternative location.
            modtime = os.stat(alternative_cache).st_mtime
            # It worked!  Use the alternative location
            cache = alternative_cache
        except OSError:
            # Neither file exists
            modtime = 0

    if (
        (not modtime and not cache_expiry) or
        (cache_expiry and time.time() - modtime > cache_expiry)
    ):
        try:
            with requests.Session() as session:
                session.mount('http://', requests.adapters.HTTPAdapter(max_retries=tries))
                session.mount('https://', requests.adapters.HTTPAdapter(max_retries=tries))
                response = session.get(location, timeout=30)
            with open(cache, 'w') as f:
                f.write(response.text)
        except IOError:
            # If we couldn't write to the specified cache location, try a
            # similar place but inside our home directory instead.
            cache = alternative_cache
            usr_dir = '/'.join(cache.split('/')[:-1])

            if not os.path.isdir(usr_dir):
                os.makedirs(usr_dir)

            with open(cache, 'w') as f:
                f.write(response.text)

    return cache
