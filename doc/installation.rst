============
Installation
============

fedmsg is available on `PyPI`_ and may also be available in your distribution's
repositories.


Fedora and EPEL
===============

fedmsg is packaged for Fedora, EPEL 6, and EPEL 7. On Fedora::

  $ sudo dnf install fedmsg

On an Enterprise Linux-based distribution with the EPEL repository::

  $ sudo yum install fedmsg


PyPI
====

To install fedmsg via PyPI, you will need the ``openssl`` header files, available
via ``openssl-devel`` on Red Hat-based distributions and via ``openssl-dev`` on
Debian-based distributions, and GCC::

  $ pip install fedmsg[commands,consumers,crypto_ng]


.. _PyPI: https://pypi.org/project/fedmsg/
