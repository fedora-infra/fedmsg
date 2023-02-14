=========
Changelog
=========

v1.1.3
======

Bug fixes
---------

* Fix the Invalid argument error
  (`#532 <https://github.com/fedora-infra/fedmsg/pull/532>`_).

* Update da.gd URL to HTTPS
  (`#528 <https://github.com/fedora-infra/fedmsg/pull/528>`_).

* Fix fedmsg-hub --with-consumers option
  (`#520 <https://github.com/fedora-infra/fedmsg/pull/520>`_)

* Require setuptools, fedmsg/meta/__init__.py imports pkg_resources
  (`#529 <https://github.com/fedora-infra/fedmsg/pull/529>`_)

* Fix compatiblity with Python 3.11+
  (`#530 <https://github.com/fedora-infra/fedmsg/pull/530>`_)

Developer improvements
----------------------

* Fix docs and lint tests
  (`#533 <https://github.com/fedora-infra/fedmsg/pull/533>`_).

Many thanks to all our contributors for this release:

* larchunix
* phuzion
* Tomáš Hrnčiar
* Miro Hrončok

v1.1.2
======

Bug fixes
---------

* Fix a DOS bug when consuming non-dict JSON messages
  (`#514 <https://github.com/fedora-infra/fedmsg/pull/514>`_).

v1.1.1
======

Bug fixes
---------

* Fix a bug in the configuration validation for ``crl_cache_expiry`` and
  ``ca_cert_cache_expiry`` (`#500 <https://github.com/fedora-infra/fedmsg/pull/500>`_).

Developer improvements
----------------------

* Fix tests using the ``ca_cert_cache`` configuration as it is deprecated
  (`#498 <https://github.com/fedora-infra/fedmsg/pull/498>`_).

* Adjust the internal ``_consume`` API for fedmsg consumers to return the
  Return any return value from the parent class's ``_consume``
  (`#507 <https://github.com/fedora-infra/fedmsg/pull/507>`_).

Contributors
------------

Thanks to all the contributors for this release:

* Sijis Aviles
* Ralph Bean
* Jeremy Cline


v1.1.0
======

Deprecations
------------

* Using URLs for the CA and CRL settings (``ca_cert_location`` and ``crl_location``
  respectively) is now deprecated and will be removed in a future release. Please
  use filesystem paths instead.

Features
--------

* Allow the CA and CRL configuration options to be file paths
  (`#484 <https://github.com/fedora-infra/fedmsg/pull/484>`_).

* All configuration settings now have defaults and validators
  (`#488 <https://github.com/fedora-infra/fedmsg/pull/488>`_).

* Strengthen "legacy protection" in fedmsg.meta by catching KeyErrors
  (`#493 <https://github.com/fedora-infra/fedmsg/pull/493>`_).


Bug fixes
---------

* Remove the duplicate dependency on ``cryptography`` from the main install
  requires (`#486 <https://github.com/fedora-infra/fedmsg/pull/486>`_).

* Adjust the x509 signing API to return text instead of bytes
  (`#495 <https://github.com/fedora-infra/fedmsg/issues/495>`_).

Development improvements
------------------------

* Alter how the tests determine if cryptography is available to work better
  with old versions of pyOpenSSL
  (`#482 <https://github.com/fedora-infra/fedmsg/pull/482>`_).


1.0.1
=====

Bug fixes
---------

* Fix an issue where messages replayed from datagrepper always failed signature
  validation despite having valid signatures
  (`#477 <https://github.com/fedora-infra/fedmsg/pull/477>`_).

* Fix a Python 3 incompatibility where the downloading the certificate revocation
  list crashed when attempting to write the file
  (`#478 <https://github.com/fedora-infra/fedmsg/pull/478>`_).


Development improvements
------------------------

* Several loggers now use their full module path as their logger name rather
  than just "fedmsg" (`#479 <https://github.com/fedora-infra/fedmsg/pull/479>`_).

Many thanks to all our contributors for this release:

* Jeremy Cline
* Chaitanya Kukde


1.0.0
=====

Backwards incompatible changes
------------------------------

* The ``--daemon`` option for all fedmsg commands that was deprecated in 0.19.0
  has been removed. We recommend using your operating system's init system instead.
  `systemd unit files <https://github.com/fedora-infra/fedmsg/tree/1.0.0/initsys>`_
  are available in the git repository (`#470 <https://github.com/fedora-infra/fedmsg/pull/470>`_).

* Python 2.6 is no longer supported (`#469 <https://github.com/fedora-infra/fedmsg/pull/469>`_).


Features
--------

* Python 3.4+ is now supported. In order to use x509 certificates to sign and verify messages,
  you will need `cryptography v1.6+ <https://cryptography.io/en/latest/>`_
  and `pyOpenSSL v16.1+ <https://pyopenssl.org/en/stable/>`_. These can be installed with pip
  via ``pip install fedmsg[crypto_ng]`` (`#449
  <https://github.com/fedora-infra/fedmsg/pull/449>`_).

* The fedmsg documentation has been re-organized (`#453
  <https://github.com/fedora-infra/fedmsg/pull/453>`_).


Development Improvements
------------------------

* The m2crypto unit tests were being skipped when the cryptography library was missing.
  This is no longer the case
  (`#446 <https://github.com/fedora-infra/fedmsg/pull/446>`_).

* All usage of the nose library has been removed from the tests and the dependency on nose
  has been removed (`#448 <https://github.com/fedora-infra/fedmsg/pull/448>`_).

* ``click`` has been added as a test dependency (`#452
  <https://github.com/fedora-infra/fedmsg/pull/452>`_).

* Test coverage increased from 54.72% to 58.82%

* Several improvements to the tox.ini file (`#458
  <https://github.com/fedora-infra/fedmsg/pull/458>`_).

Many thanks to all our contributors for this release:

* Lumír 'Frenzy' Balhar
* Ralph Bean
* Jeremy Cline
* Chenxiong Qi


0.19.1
======

0.19.1 is a bug fix release that addresses several critical regressions introduced
in 0.19.0.

Bug fixes
---------

* Fix an issue where messages failed validation because the message certificate
  and signature were unicode objects (`#456
  <https://github.com/fedora-infra/fedmsg/pull/456>`_).

* Fix an issue where message bodies were not deserialized from JSON before being
  passed to a consumer because the message bodies were unicode objects (`#464
  <https://github.com/fedora-infra/fedmsg/pull/464>`_).

* Fix an issue where messages never got passed to the consumer because the
  message pre-processing caused an unhandled exception (`#462
  <https://github.com/fedora-infra/fedmsg/pull/462>`_).


Many thanks to the contributors for this release:

* Kamil Páral
* Jeremy Cline
* Patrick Uiterwijk
* Ralph Bean
* Ricky Elrod


0.19.0
======

Deprecations
------------

* The ``--daemon`` option has been deprecated for all fedmsg commands and will be
  removed in a future release. We recommend using your operating system's init
  system instead. `systemd units and SysV init scripts
  <https://github.com/fedora-infra/fedmsg/tree/0.19.0/initsys>`_ are available in
  the git repository (`#434 <https://github.com/fedora-infra/fedmsg/pull/434>`_).


Features
--------

* A new command, ``fedmsg-signing-relay``, has been added that signs messages prior
  to relaying them (`#409 <https://github.com/fedora-infra/fedmsg/pull/409>`_).

* A new command, ``fedmsg-check``, can be used to check whether or not the expected
  fedmsg producers and consumers are running
  (`#416 <https://github.com/fedora-infra/fedmsg/pull/416>`_).

* If the message contains a ``headers`` key, these are placed in the message body
  (`#437 <https://github.com/fedora-infra/fedmsg/pull/437>`_).

* It is now possible to use `cryptography <https://cryptography.io/>`_ and
  `pyOpenSSL <https://pyopenssl.org/>`_ rather than m2crypto
  (`#421 <https://github.com/fedora-infra/fedmsg/pull/421>`_).

* The ircbot's URL shortener service is now configurable
  (`#430 <https://github.com/fedora-infra/fedmsg/pull/430>`_).


Bug fixes
---------

* Fix an issue where an ``AttributeError`` wasn't actually raised when calling
  ``fedmsg.publish`` before initializing the Moksha hub and using a non-ZeroMQ
  publishing mechanism (`#412 <https://github.com/fedora-infra/fedmsg/pull/412>`_).

* The default configuration was missing the ``topic_prefix`` key
  (`#431 <https://github.com/fedora-infra/fedmsg/pull/431>`_).


Development Improvements
------------------------

* fedmsg is now PEP-8 compliant (
  `#414 <https://github.com/fedora-infra/fedmsg/pull/414>`_,
  `#421 <https://github.com/fedora-infra/fedmsg/pull/421>`_,
  `#422 <https://github.com/fedora-infra/fedmsg/pull/422>`_).

* `Tox <https://tox.readthedocs.io/en/latest/>`_ is used to enforce PEP-8, build
  the documentation, and run the tests with multiple versions of Python
  (`#417 <https://github.com/fedora-infra/fedmsg/pull/417>`_).

* The test suite is now run with `pytest <https://docs.pytest.org/>`_ rather than nose.
  (`#417 <https://github.com/fedora-infra/fedmsg/pull/417>`_).

* Code coverage history is now tracked with
  `codecov.io <https://codecov.io/gh/fedora-infra/fedmsg/>`_.

Many thanks to all our contributors for this release:

* Elan Ruusamäe
* Pravin Chaudhary
* Ralph Bean
* Jeremy Cline


0.18.4
======

Bugs
----

* Fix an issue introduced in 0.18.3 where monitoring sockets were not being created
  in the fedmsg relay (`#433 <https://github.com/fedora-infra/fedmsg/pull/433>`_)


0.18.3
======

Features
--------

* The ``environment`` configuration key is no longer restricted to
  ``dev``, ``stg``, and ``prod``. It now must be an alphanumeric string
  (`#406 <https://github.com/fedora-infra/fedmsg/pull/406>`_).

Bug fixes
---------

* fedmsg-logger --json-input can now handle multi-line json
  (`#392 <https://github.com/fedora-infra/fedmsg/pull/392>`_).

* Update the documentation on publishing to mention the ``endpoints`` configuration
  (`#394 <https://github.com/fedora-infra/fedmsg/pull/394>`_).

* Start re-branding the library so it's not Fedora-specific
  (`#391 <https://github.com/fedora-infra/fedmsg/pull/391>`_).

* Ensure fedmsg-relay doesn't run producers
  (`#395 <https://github.com/fedora-infra/fedmsg/pull/395>`_).

* Remove keys added by datagrepper from messages retrieved from the backlog
  (`#402 <https://github.com/fedora-infra/fedmsg/pull/402>`_).


Development Improvements
------------------------

* Fix a mock used by the test suite
  (`#405 <https://github.com/fedora-infra/fedmsg/pull/405>`_).


0.18.2
======

This is a security release which addresses CVE-2017-1000001.

Bug fixes
---------

* Fixes an issue in the validation logic of the base consumer which caused
  child consumers to not validate the authenticity of messages
  (`5c21cf88a <https://github.com/fedora-infra/fedmsg/commit/5c21cf88a>`_).


0.18.1
------

Bug fixes
---------

* Only check for STOMP messages after decoding any ZMQMessage
  (`#393 <https://github.com/fedora-infra/fedmsg/pull/393>`_).


Development Improvements
------------------------

* Remove test cases for old versions of the Python six library.
  fedmsg only supports six-1.9 or greater
  (`#390 <https://github.com/fedora-infra/fedmsg/pull/390>`_).


0.18.0
======

Features
--------

* Cascade IRC connections
  (`#374 <https://github.com/fedora-infra/fedmsg/pull/374>`_).

* Get fedmsg-hub working on STOMP
  (`#380 <https://github.com/fedora-infra/fedmsg/pull/380>`_).

* Raise the resource limit on open files for fedmsg-hub
  (`#381 <https://github.com/fedora-infra/fedmsg/pull/381>`_).

* Add SSL support to irc bot
  (`#386 <https://github.com/fedora-infra/fedmsg/pull/386>`_).


Bug fixes
---------

- Return earlier when validate_signatures is turned off
  (`#388 <https://github.com/fedora-infra/fedmsg/pull/388>`_).


Documentation Improvements
--------------------------

* Remove the out-dated status page from the documentation
  (`#375 <https://github.com/fedora-infra/fedmsg/pull/375>`_).

* Make the introduction less Fedora specific
  (`#377 <https://github.com/fedora-infra/fedmsg/pull/377>`_).

* Update the necessary dependencies in the Development section
  (`#385 <https://github.com/fedora-infra/fedmsg/pull/385>`_).

* Document turning off validation for other buses
  (`#387 <https://github.com/fedora-infra/fedmsg/pull/387>`_).


Development Improvements
------------------------

- Turn testing Python 2.6 in Travis on
  (`#382 <https://github.com/fedora-infra/fedmsg/pull/382>`_).


Older Changes
=============

For older changes, consult the `old changelog
<https://github.com/fedora-infra/fedmsg/blob/0.17.2/CHANGELOG.rst>`_.
