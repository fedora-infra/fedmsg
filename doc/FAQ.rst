Frequently Asked Questions
==========================

- Is there a list of all messages?

  - Yes!  See :doc:`topics`.

- When will we be getting koji messages?

  - We have them now (we got them in late January, 2013)!  Look for
    ``org.fedoraproject.prod.buildsys...``

- When will we be getting bugzilla messages?

  - Not for a while, unfortunately.  We're waiting on Red Hat to sort out issues
    on their end with qpidd.

- Can I deploy fedmsg at my site, even if it has nothing to do with Fedora?

  - Yes.  It was designed so that all the Fedora-isms could be separated out
    into plugins.  Get in touch with ``#fedora-apps`` or create a ticket if
    you'd like to try this out.

- ``fedmsg-tail`` isn't showing the same output as the bot in the
  ``#fedora-fedmsg`` IRC channel.  What's up?

  - Is the formatting just different?  Try the following to get those "nice"
    messages::

        $ sudo dnf install python-fedmsg-meta-fedora-infrastructure
        $ fedmsg-tail --terse

  - What you were seeing before was the raw JSON content of the messages.
    That is interesting to see if you want to develop tools that consume
    fedmsg messages.  You can make those JSON blobs a little more
    readable with::

        $ fedmsg-tail --really-pretty

  - If you *really are* seeing different messages between fedmsg-bot and
    fedmsg-tail, please report it in the ``#fedora-apps`` IRC channel or
    as a `ticket on github
    <https://github.com/fedora-infra/fedmsg/issues/new>`_.

- I tried installing the ``crypto`` extra but got an error about
  something called "swig" during the M2Crypto installation.

  - If you try to install fedmsg from the Python sources (including
    PyPI), then installation may fail with an error message resembling
    the following::

        ...
        error: command 'swig' failed with exit status 1
        ...

    This happens because the M2Crypto dependency of fedmsg requires the
    non-Python package "swig" during it's compilation process.  Since
    this can't be readily expressed from within the Python ecosystem,
    the setup script (unfortunately) just assumes that it's present.

    The easiest way to avoid this problem is to install fedmsg using
    your system package manager (*e.g.*, ``dnf install fedmsg``). This
    is the recommended way to get fedmsg and has a much higher chance
    of working. (If it doesn't, then the package is likely broken, and
    the maintainer(s) will want to know about that.)

    If you have a specific reason to want to install fedmsg from
    source, then installing M2Crypto with you system package manager
    (the package is likely called something along the lines of
    ``python-m2crypto``) should satisfy the requirement and allow
    fedmsg to successfully install.  If you're unlucky and your distro
    doesn't have a packaged version of M2Crypto, then installing swig
    (which is just called plain ``swig`` in most package repositories)
    should allow M2Crypto to build successfully.
