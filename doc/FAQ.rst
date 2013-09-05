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

        $ sudo yum install python-fedmsg-meta-fedora-infrastructure
        $ fedmsg-tail --terse

  - What you were seeing before was the raw JSON content of the messages.
    That is interesting to see if you want to develop tools that consume
    fedmsg messages.  You can make those JSON blobs a little more
    readable with::

        $ fedmsg-tail --really-pretty

  - If you *really are* seeing different messages between fedmsg-bot and
    fedmsg-tail, please report it in the ``#fedora-apps`` IRC channel or
    as a `ticket on github
    <http://github.com/fedora-infra/fedmsg/issues/new>`_.

- How do I make that realtime movie of the bus?

  - Like this::

        $ sudo yum install gource
        $ sudo yum install python-fedmsg-meta-fedora-infrastructure
        $ fedmsg-tail --gource | gource -i 0 --user-image-dir ~/.cache/gravatar --log-format custom -
