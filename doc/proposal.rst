Proposal - Fedora Messaging with 0mq (``fedmsg``)
=================================================

.. contents::

This proposal reviews existing services in the Fedora infrastructure, reviews
the problem of complexity in the interaction of those services, reviews previous
work by the `Fedora Messaging SIG (special interest group)
<http://fedoraproject.org/wiki/Messaging_SIG>`_ on AMQP, and introduces an
architecture-level description of a solution using 0mq.

----

Get (or modify) the source for this document:
http://github.com/ralphbean/fedmsg

Authors:
 - Ralph Bean (threebean)

.. note:: This document should be considered `alpha`.  The original author is
   still in the process of getting familiarized with the Fedora Infrastructure.
   Feedback, criticism, and patches are as always welcome.

tl;dr
=====

We want to hook all the services in Fedora Infrastructure up to send messages to
one another over a message bus instead of communicating with each other in
heterogenous ways they do now.

We're writing a python library called ``fedmsg`` to help apps handle this more
easily.  It's built on `0mq <http://zeromq.org>`_ and `moksha
<http://moksha.fedorahosted.org>`_.

Planned Stages of development/deployment
----------------------------------------

 1) Start writing ``fedmsg``
 2) Send messages from existing services (koji, bodhi, pkgdb, fas, etc...).
 3) Consume messages for statistics, i.e. an independent statistics webapp.
 4) Consume messages for user experience, i.e. any or all of rss, email,
    gnome-shell notifications, javascript notifications in FI webapps.
 5) Consume messages for service interoperability, i.e. koji invalidates it's
    cache when it sees pkgdb messages go by on the bus.  This comes last because
    we want to make sure that message-sending works and is reliable before we
    start making existing services depend on it for their functioning.

Introduction
============

Description of the problem
--------------------------

Fedora Infrastructure is composed of a number of services (koji, fedpkg, pkgdb,
etc..) some of which are maintained outside the Fedora Project and some of which
were built in-house by the infrastructure team.  These are strung together in
a pipeline.  Think "how an upstream release becomes a package update", "How a
new source distribution becomes a package."

At present, many of the steps in this process require the maintainer to wait and
watch for a previous step to complete.  For instance once a branch of a
package is successfully built in koji, the maintainer must `submit their
update to bodhi
<http://fedoraproject.org/wiki/PackageMaintainers/UpdatingPackageHowTo#Submit_your_update_to_Bodhi>`_
(See the `new package process
<http://fedoraproject.org/wiki/New_package_process_for_existing_contributors>`_
for more details).

Other progressions in the pipeline are automated.  For instance, `AutoQA
<http://fedoraproject.org/wiki/AutoQA_architecture>`_ defines a `set of
watchers
<http://git.fedorahosted.org/git/?p=autoqa.git;a=tree;f=watchers;h=af4f6d5e68e9dfcff938d0481ac65fa52bcd1d17;hb=HEAD>`_.
Most watchers are run as a cron task.  Each one looks for `certain events
<http://git.fedorahosted.org/git/?p=autoqa.git;a=tree;f=events>`_ and fires off
tests when appropriate.

At LinuxFest Northwest (2009), jkeating gave `a talk
<http://jkeating.fedorapeople.org/lfnw-messaging-2009.pdf>`_ on the problem of
complexity in the Fedora infrastructure and how this might be addressed with a
message bus architecture.  Each service in the infrastructure depends on
many of the others.  Some pieces directly poke others:  git (fedpkg) currently
pokes AutoQA from a post-update hook.  Other pieces poll others' status:  koji
scrapes pkgdb for package-owner relationships and email aliases.

This dense coupling of services makes changing, adding, or replacing services
more complicated:  commits to one project require a spidering of code changes
to all the others.

How messaging might address the problem
---------------------------------------

jkeating's `talk on messaging in the Fedora Instructure
<http://jkeating.fedorapeople.org/lfnw-messaging-2009.pdf>`_ proposed the
adoption of a unified message bus to reduce the complexity of multiple
interdependent services.  Instead of a service interfacing with its
dependencies' implementations, it could subscribe to a `topic`, provide a
callback, and respond to events.

For instance, instead of having koji scrape pkgdb on an interval for changed
email addresses, pkgdb could emit messages to the
``org.fedoraproject.service.pkgdb`` topic whenever an account's email address
changes.  koji could subscribe to the same topic and provide a callback that
updates its local email aliases when invoked.

In another case, the git (fedpkg) post-update hook could publish messages to
the ``org.fedoraproject.service.fedpkg.post-update`` topic.  AutoQA could
subscribe to the same.  Now if we wanted to enable another service to act when
updates are pushed to fedpkg, that service need only subscribe to the topic and
implement its own callback instead of appending its own call to fedpkg's
post-update hook (instead of coupling its own implementation with fedpkg's).

A message bus architecture, once complete, would dramatically reduce the work
required to update and maintain services in the Fedora infrastructure.

Other benefits
--------------

By adopting a messaging strategy for Fedora Infrastructure we could gain:

 - A stream of data which we can watch and from which we can garner statistics
   about infrastructure activity.
 - The de-coupling of services from one another.
 - libnotify notifications to developers' desktops.
 - jquery.gritter.js notifications to web interfaces.

   - this could be generalized to a ``fedmsg.wsgi`` middleware layer that
     injects a fedora messaging dashboard header into every page served by apps
     `X`, `Y`, and `Z`.

 - An irc channel, #fedora-firehose that echoes every message on the bus.
 - An identi.ca account, @fedora-firehose, that echoes every message on the bus.

AMQP, QMF, and 0mq
==================

AMQP and QMF or "Broker?  Damn near killed 'er!"
------------------------------------------------

When discussions on the `Fedora Messaging SIG
<http://fedoraproject.org/wiki/Messaging_SIG>`_ began, AMQP was the choice by
default.  Since then members of the SIG have become attracted to an alternative
messaging interface called `0mq <http://www.zeromq.org>`_.

Recommended reading:

 - `What's wrong with AMQP
   <http://www.imatix.com/articles:whats-wrong-with-amqp>`_

The following is recreated from J5's Publish/Subscribe Messaging Proposal
as an example of how Fedora Infrastructure could be reorganized with AMQP
and a set of federated AMQP brokers (qpid).

.. image:: https://github.com/ralphbean/fedmsg/raw/develop/doc/_static/reorganize-amqp-j5.png

The gist is that each service in the Fedora Infrastructure would have the
address of a central message broker on hand.  On startup, each service would
connect to that broker, ask the broker to establish its outgoing queues, and
begin publishing messages.  Similarly, each service would ask the broker to
establish incoming queues for them.  The broker would handle the routing of
messages based on ``routing_keys`` (otherwise known as `topics`) from each
service to the others.

The downshot, in short, is that AMQP requires standing up a single central
broker and thus a single-point-of-failure.  In the author's work on `narcissus
<http://narcissus.rc.rit.edu>`_ I found that for even the most simple of AMQP
configurations, my qpid brokers' queues would bloat over time until \*pop\*,
the broker would fall over.

TODO -- write about QMF

0mq or "Going for Broke(rless)"
-------------------------------

0mq is developed by a team that had a hand in the original development of AMQP.
It claims to be a number of things: an "intelligent transport layer",
a "socket library that acts as a concurrency framework", and the `sine qua non`
"Extra Spicy Sockets!"

Recommended reading:
 - `The Z-guide <http://zguide.zeromq.org/page:all>`_

The following depicts an overview of a subset of Fedora Infrastructure
organized with a decentralized 0mq bus parallel to the spirit of J5's
recreated diagram in the AMQP section above.

.. image:: https://github.com/ralphbean/fedmsg/raw/develop/doc/_static/reorganize-0mq-overview.png

No broker.  The gist is that each service will open a port and begin
publishing messages ("bind to" in zmq-language).  Each other service will
connect to that port to begin consuming messages.  Without a central broker
doing `all the things
<http://www.imatix.com/articles:whats-wrong-with-amqp>`_, 0mq can afford a high
throughput.  For instance, in initial tests of a 0mq-enabled `moksha hub
<http://moksha.fedorahosted.org>`_, the Fedora Engineering Team achieved a
100-fold speedup over AMQP.

Service discovery
~~~~~~~~~~~~~~~~~

Shortly after you begin thinking over how to enable Fedora Infrastructure to
pass messages over a `fabric` instead of to a `broker`, you arrive at the
problem we'll call "service discovery".

In reality, (almost) every service both `produces` and `consumes` messages.  For
the sake of argument, we'll talk here just about a separate `producing
service` and some `consuming services`.

Scenario:  the producing service starts up, producing socket (with a hidden
queue), and begins producing messages.  Consuming services `X`, `Y`, and `Z`
are interested in this and they would like to connect.

With AMQP, this is simplified.  You have one central broker and each consuming
service need only know it's one address.  They connect and the match-making is
handled for them.  With 0mq, each consuming service needs to somehow
`discover` its producer(s) address(es).

There are a number of ways to address this:

 - *Write our own broker*; this would not be that difficult.  We could (more
   simply) scale back the project and write our own directory lookup service
   that would match consumers with their providers.  This could be done in
   surprisingly few lines of python.  This issue is that we re-introduce the
   sticking point of AMQP, a single point of failure.

 - *Use DNS*; There is a helpful `blog post
   <http://www.ceondo.com/ecte/2011/12/dns-zeromq-services>`_ on how to do this
   with `djbdns`.  DNS is always there anyways: if DNS goes down, we have bigger
   things to worry about than distributing updates to our messaging topology.

 - *Share a raw text file*; This at first appears crude and cumbersome:

   - Maintain a list of all `fedmsg`-enabled producers in a text file
   - Make sure that file is accessible from every consuming service.
   - Have each consuming service read in the file and connect to every
     (relevant) producer in the list

In my opinion, using DNS is generally speaking the most elegant solution.
However, for Fedora Infrastructure in particular, pushing updates to DNS and
pushing a raw text file to every server involves much-the-same workflow:
`puppet`.  Because much of the overhead of updating the text file falls in-line
with the rest of Infrastructure work, it makes more sense to go with the third
option.  Better not to touch DNS when we don't have to.

TODO -- where exactly will that file live?
TODO -- what is that file's format?

sparse topics
-------------

Different buses
---------------

- critical and statistical buses (critical is subset of statistical).

Authn, authz
------------

(func has certs laying around already).

network load
------------

- calculate network load -
http://lists.zeromq.org/pipermail/zeromq-dev/2010-August/005254.html

fringe services
---------------

- example of building a relay that condenses messages from `n`
  proxies and re-emits them.
- example of bridging amqp and 0mq
- bugzilla-push - https://github.com/LegNeato/bugzilla-push




Namespace considerations
------------------------

In the above examples, the topic names are derived from the service names.
For instance, pkgdb publishes messages to
``org.fedoraproject.service.pkgdb*``, AutoQA presumably publishes messages
to ``org.fedoraproject.service.autoqa*``, and so on.

This convention, while clear-cut, has its limitations.  Say we wanted to
replace pkgdb whole-sale with our shiney new `threebean-db` (tm).  Here,
all other services are subscribed to topics that mention pkgdb explicitly.
Rolling out threebean-db will require patching every other service; we find
ourselves in a new flavor of the same complexity/co-dependency trap
described in the first section.

The above `service-oriented` topic namespace is one option.
Consider an `object-oriented` topic namespace where the objects are things
like users, packages, builds, updates, tests, tickets, and composes.  Having
bodhi subscribe to ``org.fedoraproject.object.tickets`` and
``org.fedoraproject.object.builds`` leaves us less tied down to the current
implementation of the rest of the infrastructure.  We could replace `bugzilla`
with `pivotal` and bodhi would never know the difference - a ticket is a
ticket.

That would be nice; but there are too many objects in Fedora Infrastructure that
would step on each other.  For instance, Koji **tags** packages and Tagger
**tags** packages; these two are very different things.  Koji and Tagger cannot
**both** emit events over ``org.fedoraproject.package.tag.*`` without widespread
misery.

Consequently, our namespace follows a `service-oriented` pattern.

The scheme
----------

Event topics will follow the rule::

 org.fedoraproject.ENV.SERVICE.OBJECT[.SUBOBJECT].EVENT

Where:

 - ``ENV`` is one of `dev`, `stg`, or `production`.
 - ``SERVICE`` is something like `koji`, `bodhi`, or `fedoratagger`
 - ``OBJECT`` is something like `package`, `user`, or `tag`
 - ``SUBOBJECT`` is something like `owner` or `build` (in the case where
   ``OBJECT`` is `package`, for instance)
 - ``EVENT`` is a verb like `update`, `create`, or `complete`.

All 'fields' in a topic **must**:

 - Be `singular` (Use `package`, not `packages`)
 - Use existing fields as much as possible (since `complete` is already used
   by other topics, use that instead of using `finished`).


Code Examples - 0mq and ``fedmsg``
==================================

This package (the `package containing the docs you are reading right now
<http://github.com/ralphbean/fedmsg>`_) is ``fedmsg``.  It aims to be a wrapper
around calls to the `moksha hub <http://moksha.fedorahosted.org>`_ API that:

 - Handles Fedora-Infra authn/authz
 - Handles Fedora-Infra service discovery
 - Helps you avoid topic and message content typos.
 - Gets in your way as little as possible

Examples of emitting events
---------------------------

Here's a real dummy test::

    >>> import fedmsg
    >>> fedmsg.send_message(topic='testing', modname='test', msg={
    ...     'test': "Hello World",
    ... })

The above snippet will send the message ``'{test: "Hello World"}'`` message
over the ``org.fedoraproject.dev.test.testing`` topic.
The ``modname`` argument will be omitted in most use cases.  By default,
``fedmsg`` will try to guess the name of the module that called it and use
that to produce an intelligent topic.
Specifying ``modname`` argues that ``fedmsg`` not be `too smart`.

Here's an example from
`fedora-tagger <http://github.com/ralphbean/fedora-tagger>`_ that sends the
information about a new tag over
``org.fedoraproject.{dev,stg,prod}.fedoratagger.tag.update``::

    >>> import fedmsg
    >>> fedmsg.send_message(topic='tag.update', msg={
    ...     'user': user,
    ...     'tag': tag,
    ... })

Note that the `tag` and `user` objects are SQLAlchemy objects defined by
tagger.  They both have ``.__json__()`` methods which ``.send_message``
uses to convert both objects to stringified JSON for you.

``fedmsg`` has also guessed the module name (``modname``) of it's caller and
inserted it into the topic for you.  The code from which we stole the above
snippet lives in ``fedoratagger.controllers.root``.  ``fedmsg`` figured that
out and stripped it down to just ``fedoratagger`` for the final topic of
``org.fedoraproject.{dev,stg,prod}.fedoratagger.tag.update``.

Examples of consuming events
----------------------------

TODO

Console Scripts
---------------

It makes sense for ``fedmsg`` to also provide a number of console scripts for
use with random shell scripts or with nagios, for instance.

Currently we have implemented:

 - ``fedmsg-status`` - checks the status of all registered producers by
   listening for a heartbeat.
 - ``fedmsg-logger`` - sends messages over the ``org.fedoraproject.dev.logger``
   topic.

Systems and Events
==================

All messages will be transmitted as stringified JSON.

List of systems, their events, and associated fields
----------------------------------------------------

Each item here is a service followed by the list of events that it emits.  Each
event is followed by a list of services that will likely consume that event.

----

 - AutoQA

   - ``org.fedoraproject.{stg,prod}.autoqa.package.tests.complete`` -> koji, bodhi, fcomm

 - Bodhi

   - ``org.fedoraproject.{stg,prod}.bodhi.update.request{.TYPE}`` -> fcomm, autoqa
   - ``org.fedoraproject.{stg,prod}.bodhi.update.complete{.TYPE}`` -> fcomm, autoqa
   - ``org.fedoraproject.{stg,prod}.bodhi.update.push`` -> fcomm
   - ``org.fedoraproject.{stg,prod}.bodhi.update.remove`` -> fcomm

 - Bugzilla

   - ``org.fedoraproject.{stg,prod}.bugzilla.bug.create`` -> fcomm
   - ``org.fedoraproject.{stg,prod}.bugzilla.bug.update`` -> fcomm

 - Compose

   - ``org.fedoraproject.{stg,prod}.compose.compose.complete`` -> mirrormanager, autoqa

 - Elections (TODO -- what is the app called?)

   - ``org.fedoraproject.{stg,prod}.elections...``  <-- TODO.  Objects and events?

 - FAS

   - ``org.fedoraproject.{stg,prod}.fas.user.update`` -> fcomm
   - ``org.fedoraproject.{stg,prod}.fas.group.update`` -> fcomm

 - Koji -- FIXME, `tags` from ``koji`` conflict with `tags` from ``tagger``

   - ``org.fedoraproject.{stg,prod}.koji.tag.build`` -> secondary arch koji
   - ``org.fedoraproject.{stg,prod}.koji.tag.create`` -> secondary arch koji
   - ``org.fedoraproject.{stg,prod}.koji.package.build.complete`` -> fcomm, secondary arch koji,
     SCM, autoqa, sigul
   - ``org.fedoraproject.{stg,prod}.koji.package.build.start`` -> fcomm
   - ``org.fedoraproject.{stg,prod}.koji.package.build.fail`` -> fcomm

 - MeetBot (supybot?)

   - ``org.fedoraproject.{stg,prod}.irc.meeting.start``
   - ``org.fedoraproject.{stg,prod}.irc.meeting.complete``

 - NetApp -- FIXME, the topics from netapp should be reviewed.  They seem
   ambiguous.

   - ``org.fedoraproject.{stg,prod}.netapp.sync.stop`` -> mirrormanager
   - ``org.fedoraproject.{stg,prod}.netapp.sync.resume`` -> mirrormanager

 - PkgDB

   - ``org.fedoraproject.{stg,prod}.pkgdb.package.create`` -> koji, secondary arch koji, bugzilla
   - ``org.fedoraproject.{stg,prod}.pkgdb.package.remove`` -> koji, secondary arch koji,
   - ``org.fedoraproject.{stg,prod}.pkgdb.package.rename`` -> bugzilla
   - ``org.fedoraproject.{stg,prod}.pkgdb.package.retire`` -> SCM
   - ``org.fedoraproject.{stg,prod}.pkgdb.package.owner.update`` -> koji, secondary arch koji, bugzilla
   - TODO - lots of ``org.fp.user...`` events to detail here.

 - SCM

   - ``org.fedoraproject.{stg,prod}.scm.repo.checkin`` -> fcomm, autoqa

 - Tagger

   - ``org.fedoraproject.{stg,prod}.fedoratagger.tag.create`` -> fcomm, pkgdb
   - ``org.fedoraproject.{stg,prod}.fedoratagger.tag.remove`` -> fcomm, pkgdb
   - ``org.fedoraproject.{stg,prod}.fedoratagger.tag.update`` -> fcomm, pkgdb
   - ``org.fedoraproject.{stg,prod}.fedoratagger.user.rank.update`` -> fcomm, (pkgdb?)
   - ``org.fedoraproject.{stg,prod}.fedoratagger.login`` -> ??

 - Wiki

   - ``org.fedoraproject.{stg,prod}.wiki....``

 - Zabbix

   - ``org.fedoraproject.{stg,prod}.zabbix.service.update`` -> fcomm
