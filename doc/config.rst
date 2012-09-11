Configuration
=============

.. automodule:: fedmsg.config
    :members:
    :undoc-members:
    :show-inheritance:

.. autofunction:: fedmsg.init

Glossary of Configuration Values
--------------------------------

.. glossary::

    sign_messages
        ``bool`` - If set to true, then :mod:`fedmsg.core` will try to sign
        every message sent using the machinery from :mod:`fedmsg.crypto`.

        It is often useful to set this to `False` when developing.  You may not
        have X509 certs or the tools to generate them just laying around.  If
        disabled, you will likely want to also disable
        :term:`validate_signatures`.

    validate_signatures
        ``bool`` - If set to true, then the base class
        :class:`fedmsg.consumers.FedmsgConsumer` will try to use
        :func:`fedmsg.crypto.validate` to validate messages before handing
        them off to the particular consumer for which the message is bound.

        This is also used by :mod:`fedmsg.text` to denote trustworthiness
        in the natural language representations produced by that module.

    ssldir
        ``str`` - This should be directory on the filesystem
        where the certificates used by :mod:`fedmsg.crypto` can be found.
        Typically ``/etc/pki/fedmsg/``.

    crl_location
        ``str`` - This should be a URL where the certificate revocation list can
        be found.  This is checked by :func:`fedmsg.crypto.validate` and
        cached on disk.

    crl_cache
        ``str`` - This should be the path to a filename on the filesystem where
        the CRL downloaded from :term:`crl_location` can be saved.  The python
        process should have write access there.

    crl_cache_expiry
        ``int`` - Number of seconds to keep the CRL cached before checking
        :term:`crl_location` for a new one.

    certnames
        ``dict`` - This should be a mapping of certnames to cert prefixes.

        The keys should be of the form ``<service>.<host>``.  For example:
        ``bodhi.app01``.

        The values should be the prefixes of cert/key pairs to be found in
        :term:`ssldir`.  For example, if
        ``bodhi-app01.stg.phx2.fedoraproject.org.crt`` and
        ``bodhi-app01.stg.phx2.fedoraproject.org.key`` are to be found in
        :term:`ssldir`, then the value
        ``bodhi-app01.stg.phx2.fedoraproject.org`` should appear in the
        :term:`certnames` dict.

        Putting it all together, this value could be specified as follows::

            certnames={
                "bodhi.app01": "bodhi-app01.stg.phx2.fedoraproject.org",
                # ... other certname mappings may follow here.
            }

        .. note::

            This is one of the most cumbersome parts of fedmsg.  The reason we
            have to enumerate all these redundant mappings between
            "service.hostname" and "service-fqdn" has to do with the limitations
            of reverse dns lookup.  Case in point, try running the following on
            app01.stg inside Fedora Infrastructure's environment.

                >>> import socket
                >>> print socket.getfqdn()

            You might expect it to print "app01.stg.phx2.fedoraproject.org", but
            it doesn't.  It prints "memcached04.phx2.fedoraproject.org".  Since
            we can't rely on programatically extracting the fully qualified
            domain names of the host machine during runtime, we need to
            explicitly list all of the certs in the config.
