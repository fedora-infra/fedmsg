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

    topic_prefix
        ``str`` - A string prefixed to the topics of all outgoing messages.
        Typically "org.fedoraproject".  Used when :func:`fedmsg.publish`
        constructs the fully-qualified topic for an outgoing message.

    environment
        ``str`` - A string that must be one of ``['prod', 'stg', 'dev']``.  It
        signifies the environment in which this fedmsg process is running and
        can be used to weakly separate different logical buses running in the
        same infrastructure.  It is used by :func:`fedmsg.publish` when it is
        constructing a fully-qualified topic.

    high_water_mark
        ``int`` - An option to zeromq that specifies a hard limit on the maximum
        number of outstanding messages to be queued in memory before reaching an
        exceptional state.

        For our pub/sub zeromq sockets, the exceptional state means *dropping
        messages*.  See the upstream documentation for `ZMQ_HWM
        <http://api.zeromq.org/2-1:zmq-setsockopt>`_ and `ZMQ_PUB
        <http://api.zeromq.org/2-1:zmq-socket>`_.

        A :term:`high_water_mark` of ``0`` means "no limit" and is the
        recommended value for fedmsg.  It is referenced when initializing
        sockets in :func:`fedmsg.init`.

    io_threads
        ``int`` - An option that specifies the size of a zeromq thread pool to
        handle I/O operations.  See the upstream documentation for `zmq_init
        <http://api.zeromq.org/2-1:zmq-init>`_.

        This value is referenced when initializing the zeromq context in
        :func:`fedmsg.init`.

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

    zmq_enabled
        ``bool`` - A value that must be true.  It is present solely
        for compatibility/interoperability with `moksha
        <http://mokshaproject.net>`_.

    zmq_strict
        ``bool`` - When false, allow splats ('*') in topic names when
        subscribing.  When true, disallow splats and accept only strict matches
        of topic names.

        This is an argument to `moksha <http://mokshaproject.net>`_ and arose
        there to help abstract away differences between the "topics" of zeromq
        and the "routing_keys" of AMQP.
