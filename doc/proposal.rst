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
``org.fedoraproject.services.pkgdb`` topic whenever an account's email address
changes.  koji could subscribe to the same topic and provide a callback that
updates its local email aliases when invoked.

In another case, the git (fedpkg) post-update hook could publish messages to
the ``org.fedoraproject.services.fedpkg.post-update`` topic.  AutoQA could
subscribe to the same.  Now if we wanted to enable another service to act when
updates are pushed to fedpkg, that service need only subscribe to the topic and
implement its own callback instead of appending its own call to fedpkg's
post-update hook (instead of coupling its own implementation with fedpkg's).

A message bus architecture, once complete, would dramatically reduce the work
required to update and maintain services in the Fedora infrastructure.

Namespace considerations
------------------------

In the above examples, the topic names are derived from the service names.
For instance, pkgdb publishes messages to
``org.fedoraproject.services.pkgdb*``, AutoQA presumably publishes messages
to ``org.fedoraproject.services.autoqa*``, and so on.

This convention, while clear-cut, has its limitations.  Say we wanted to
replace pkgdb whole-sale with our shiney new `threebean-db` (tm).  Here,
all other services are subscribed to topics that mention pkgdb explicitly.
Rolling out threebean-db will require patching every other service; we find
ourselves in a new flavor of the same complexity/co-dependency trap
described in the first section.

The above `service-oriented` topic namespace is one option.
Consider an `object-oriented` topic namespace where the objects are things
like users, packages, builds, updates, tests, tickets, and composes.  Having
bodhi subscribe to ``org.fedoraproject.objects.tickets`` and
``org.fedoraproject.objects.builds`` leaves us less tied down to the current
implementation of the rest of the infrastructure.  We could replace `bugzilla`
with `pivotal` and bodhi would never know the difference - a ticket is a
ticket.

TODO - Decide: which namespace convention will we adopt?

Other benefits
==============

By adopting a messaging strategy for Fedora Infrastructure we could gain:

 - A stream of data which we can watch and from which we can garner statistics
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


*TODO*
 - introduce AMQP

   - introduce QMF

 - introduce 0mq

   - critical and statistical buses (critical is subset of statistical).
   - calculate network load -
     http://lists.zeromq.org/pipermail/zeromq-dev/2010-August/005254.html
   - auth (func has certs laying around already).
   - service discovery

     - dns
     - txt file

Examples of reorganization
--------------------------

*TODO*:

 - present flow diagram
 - AMQP flow diagram
 - various 0mq flow diagrams

   - example of building a relay that condenses messages from `n` proxies and
     re-emits them.

Code Examples
=============

Examples of emitting events
---------------------------

.. make these into doc-tests where possible

*TODO* -- bugzilla-push - https://github.com/LegNeato/bugzilla-push

Examples of consuming events
----------------------------


Systems and Events
==================

All messages will be transmitted as stringified JSON.

List of systems, their events, and associated fields
----------------------------------------------------

Each item here is a service followed by the list of events that it emits.  Each
event is followed by a list of services that will likely consume that event.

.. note:: This could use a lot of help.  For instance, should the
   ``org.fedoraproject.koji.package.testing.complete`` event really be emitted
   from koji?  Or renamed and emitted from AutoQA for consumption by koji?

----

 - AutoQA

   - ``org.fedoraproject.autoqa.package.complete`` -> koji, bodhi, fcomm

 - Bodhi

   - ``org.fedoraproject.bodhi.update.request`` -> fcomm, autoqa
   - ``org.fedoraproject.bodhi.update.push`` -> fcomm
   - ``org.fedoraproject.bodhi.update.remove`` -> fcomm

 - Bugzilla

   - ``org.fedoraproject.bugzilla.bug.new`` -> fcomm
   - ``org.fedoraproject.bugzilla.bug.update`` -> fcomm

 - Compose

   - ``org.fedoraproject.compose.complete`` -> mirrormanager, autoqa

 - FAS

   - ``org.fedoraproject.fas.user.update`` -> fcomm

 - Koji

   - ``org.fedoraproject.koji.tag.build`` -> secondary arch koji
   - ``org.fedoraproject.koji.tag.create`` -> secondary arch koji
   - ``org.fedoraproject.koji.package.build.complete`` -> fcomm, secondary arch koji,
     SCM, autoqa, sigul
   - ``org.fedoraproject.koji.package.build.start`` -> fcomm
   - ``org.fedoraproject.koji.package.build.fail`` -> fcomm
   - ``org.fedoraproject.koji.package.new`` -> secondary arch koji
   - ``org.fedoraproject.koji.package.owner.update`` -> secondary arch koji
   - ``org.fedoraproject.koji.package.remove`` -> secondary arch koji

 - NetApp

   - ``org.fedoraproject.netapp.sync.stop`` -> mirrormanager
   - ``org.fedoraproject.netapp.sync.resume`` -> mirrormanager

 - PkgDB

   - ``org.fedoraproject.pkgdb.package.new`` -> koji, bugzilla
   - ``org.fedoraproject.pkgdb.package.remove`` -> koji
   - ``org.fedoraproject.pkgdb.package.rename`` -> bugzilla
   - ``org.fedoraproject.pkgdb.package.retire`` -> SCM
   - ``org.fedoraproject.pkgdb.package.owner.update`` -> koji, bugzilla

 - SCM

   - ``org.fedoraproject.scm.checkin`` -> fcomm, autoqa

 - Tagger

   - ``org.fedoraproject.tagger.tag.update`` -> fcomm, pkgdb
   - ``org.fedoraproject.tagger.tag.new`` -> fcomm, pkgdb
   - ``org.fedoraproject.tagger.user.rank.update`` -> fcomm

 - XTeddy

   - ``org.fedoraproject.xteddy.love`` -> everyone

 - Zabbix

   - ``org.fedoraproject.zabbix.service.update`` -> fcomm
