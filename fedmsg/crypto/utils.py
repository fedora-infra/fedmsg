import logging
import requests


# A simple dictionary to cache certificates in
_cached_certificates = dict()

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


def load_certificates(ca_location, crl_location=None, invalidate_cache=False):
    """
    Load the CA certificate and CRL, caching it for future use.

    .. note::
        Providing the location of the CA and CRL as an HTTPS URL is deprecated
        and will be removed in a future release.

    Args:
        ca_location (str): The location of the Certificate Authority certificate. This should
            be the absolute path to a PEM-encoded file. It can also be an HTTPS url, but this
            is deprecated and will be removed in a future release.
        crl_location (str): The location of the Certificate Revocation List. This should
            be the absolute path to a PEM-encoded file. It can also be an HTTPS url, but
            this is deprecated and will be removed in a future release.
        invalidate_cache (bool): Whether or not to invalidate the certificate cache.

    Returns:
        tuple: A tuple of the (CA certificate, CRL) as unicode strings.

    Raises:
        requests.exception.RequestException: Any exception requests could raise.
        IOError: If the location provided could not be opened and read.
    """
    if crl_location is None:
        crl_location = ''

    try:
        if invalidate_cache:
            del _cached_certificates[ca_location + crl_location]
        else:
            return _cached_certificates[ca_location + crl_location]
    except KeyError:
        pass

    ca, crl = None, None
    if ca_location:
        ca = _load_certificate(ca_location)
    if crl_location:
        crl = _load_certificate(crl_location)

    _cached_certificates[ca_location + crl_location] = ca, crl
    return ca, crl


def _load_certificate(location):
    """
    Load a certificate from the given location.

    Args:
        location (str): The location to load. This can either be an HTTPS URL or an absolute file
            path. This is intended to be used with PEM-encoded certificates and therefore assumes
            ASCII encoding.

    Returns:
        str: The PEM-encoded certificate as a unicode string.

    Raises:
        requests.exception.RequestException: Any exception requests could raise.
        IOError: If the location provided could not be opened and read.
    """
    if location.startswith('https://'):
        _log.info('Downloading x509 certificate from %s', location)
        with requests.Session() as session:
            session.mount('https://', requests.adapters.HTTPAdapter(max_retries=3))
            response = session.get(location, timeout=30)
            response.raise_for_status()
            return response.text
    else:
        _log.info('Loading local x509 certificate from %s', location)
        with open(location, 'rb') as fd:
            return fd.read().decode('ascii')
