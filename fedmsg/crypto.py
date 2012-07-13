""" Cryptographic component of fedmsg.

In general, we assume that 'everything on the bus is public'.  Even though all
the zmq endpoints are firewalled off from the outside world with iptables, we
intend to someday have a forwarding service setup that will indiscriminantly
forward all messages to anyone who wants them.  So, the issue is not encrypting
messages so they can't be read.  It is up to sensitive services like FAS to
*not send* sensitive information in the first place (like passwords, for
instance).

Since at some point, some services will respond to and act on messages that
come across the bus, we need facilities for guaranteeing a message comes from
where it *ought* to come from.  (Tangentially, message consumers need a simple
way to declare where they expect their messages to come from and have
the filtering and validation handled for them).

There should also be a convenient way to turn crypto off both globally and
locally.  Justification: a developer may want to work out a bug without any
messages being signed or validated.  In production, certain senders may send
non-critical data from a corner of Fedora Infrastructure in which it's
difficult to sign messages.  A consumer of those messages should be allowed
to ignore validation for those and only those expected unsigned messages

This module encapsulates standalone functions for:

    - Message signing.
    - Signature validation.

To accomplish this, we'll use puppet's already in place PKI involving X509
certificates and RSA signatures.
"""


import copy

import fedmsg.json

import logging
log = logging.getLogger('fedmsg')

try:
    import M2Crypto
    # FIXME - m2ext will be unnecessary once the following bug is closed.
    # https://bugzilla.osafoundation.org/show_bug.cgi?id=11690
    import m2ext
except ImportError, e:
    log.warn("Crypto disabled %r" % e)


def sign(message, ssldir, certname, **config):
    """ Insert two new fields into the message dict and return it.

        'signature' - the computed RSA message digest of the JSON repr.
        'certificate' - the base64 X509 certificate of the sending host.
    """

    certificate = M2Crypto.X509.load_cert(
        "%s/certs/%s.pem" % (ssldir, certname)).as_pem()
    # FIXME ? -- Opening this file requires elevated privileges in stg/prod.
    rsa_private = M2Crypto.RSA.load_key(
        "%s/private_keys/%s.pem" % (ssldir, certname))

    signature = rsa_private.sign_rsassa_pss(fedmsg.json.dumps(message))

    # Return a new dict containing the pairs in the original message as well
    # as the new authn fields.
    return dict(message.items() + [
        ('signature', signature.encode('base64')),
        ('certificate', certificate.encode('base64')),
    ])


def validate(message, ssldir, **config):
    """ Return true or false if the message is signed appropriately.

    Three things must be true:

      1) The X509 cert must be signed by our CA
      2) The cert must not be in our CRL.
      3) We must be able to verify the signature using the RSA public key
         contained in the X509 cert.

    Later, a consumer may check that the name on the cert matches the name from
    which they expect a message of this type to originate.
    """

    # TODO -- expose the cert name to the Consumer API so it can do more
    #         fine-grained checks.

    def fail(reason):
        log.warn("Failed validation.  %s" % reason)
        return False

    # Some sanity checking
    for field in ['signature', 'certificate']:
        if not field in message:
            return fail("No %r field found." % field)

    # Peal off the auth datums
    decode = lambda obj: obj.decode('base64')
    signature, certificate = map(decode, (
        message['signature'], message['certificate']))
    message = strip_credentials(message)

    # Build an X509 object
    cert = M2Crypto.X509.load_cert_string(certificate)

    # Validate the cert.  Make sure it is signed by our CA.
    #   validate_certificate will one day be a part of M2Crypto.SSL.Context
    #   https://bugzilla.osafoundation.org/show_bug.cgi?id=11690
    # FIXME -- the CRL is not actually checked here.
    ctx = m2ext.SSL.Context()
    ctx.load_verify_locations(cafile="%s/certs/ca.pem" % ssldir)
    if not ctx.validate_certificate(cert):
        return fail("X509 certificate is not valid.")

    # If the cert is good, then test to see if the signature in the messages
    # matches up with the provided cert.
    rsa_public = cert.get_pubkey().get_rsa()
    if not rsa_public.verify_rsassa_pss(fedmsg.json.dumps(message), signature):
        return fail("RSA signature failed to validate.")

    return True


def strip_credentials(message):
    """ Strip credentials from a message dict. """
    message = copy.deepcopy(message)
    for field in ['signature', 'certificate']:
        if field in message:
            del message[field]
    return message
