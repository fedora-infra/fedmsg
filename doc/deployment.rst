Deploying fedmsg for yourself
=============================

Elsewhere, the emphasis in fedmsg docs is on how to subscribe to an existing fedmsg
deployment; how do I listen for koji builds from Fedora Infrastructure?  This
document, on the other hand, is directed at those who want to deploy fedmsg for
their own systems.

This document also only goes as far as setting things up for a single machine.
You typically deploy fedmsg across an *infrastructure* but if you just want to
try it out for "proof-of-concept", these are the docs for you.

Lastly, the emphasis here is on the practical -- there will be lots of
examples.  There is plenty of long-winded explanation over at :doc:`overview`.

.. note:: Caveat:  fedmsg is deployed at a couple different sites:

   - Fedora Infrastructure
   - `data.gouv.fr <http://data.gouv.fr>`_
   - to some extent, Debian Infrastructure

   We wrote this document much later afterwards, so, if you come across errors,
   or things that don't work right.  Please `report it
   <https://github.com/fedora-infra/fedmsg/issues/new>`_.

The basics
----------

First install fedmsg::

    $ sudo dnf install fedmsg

Now you have some ``fedmsg-*`` cli tools like ``fedmsg-tail`` and
``fedmsg-logger``.

On Fedora systems, fedmsg is configured by default to subscribe to Fedora
Infrastructure's bus.  Since you are deploying for your own site, you don't
want that.  So edit ``/etc/fedmsg.d/endpoints.py`` and *comment out the whole
"fedora-infrastructure" section*, like this:

.. code-block:: python

    #"fedora-infrastructure": [
    #    "tcp://hub.fedoraproject.org:9940",
    #    #"tcp://stg.fedoraproject.org:9940",
    #],

Starting fedmsg-relay
---------------------

Not all fedmsg interactions require the relay, but publishing messages from a
terminal does.

Install fedmsg-relay and start it::

    $ sudo dnf install fedmsg-relay
    $ sudo systemctl restart fedmsg-relay
    $ sudo systemctl enable fedmsg-relay

It has a pid file in ``/var/run/fedmsg/fedmsg-relay.pid`` and you can view the
logs in ``journalctl --follow``.  On other systems you can find the logs in
``/var/log/fedmsg/fedmsg-relay.log``.

Out of the box, it should be listening for incoming messages on
``tcp://127.0.0.1:2003`` and re-publishing them indiscriminately at
``tcp://127.0.0.1:4001``.  It is fine to keep these defaults.

Test it out
-----------

Try a test!  Open two terminals:

- In the first, type ``fedmsg-tail --really-pretty``
- In the second, type ``echo "Hello world" | fedmsg-logger``

You should see the JSON representation of your message show up in the first
terminal.  It should look something like this.

.. code-block:: javascript

    {
      "username": "root", 
      "i": 1, 
      "timestamp": 1393878837, 
      "msg_id": "2014-f1c49f0b-5caf-49e6-b79a-cc54bcfac602", 
      "topic": "org.fedoraproject.dev.logger.log", 
      "msg": {
        "log": "Hello world"
      }
    }

These are two handy tools for debugging the configuration of your
bus.

Branching out to two machines
-----------------------------

Everything is tied together in fedmsg by the :term:`endpoints` dict.  It lets

- A publishing service know what port it should be publishing on.
- A consuming service know where the publisher is so it can connect there.

Let's say you have two machines ``hostA`` and ``hostB``.  If you installed that
fedmsg-relay on ``hostA`` as discussed above, then the config file in
``/etc/fedmsg.d/relay.py`` is going to have values like
``tcp://127.0.0.1:4001``.  That address will only work for local connectivity.
Try changing *all* occurences of ``127.0.0.1`` in that file to ``hostA`` so
that it looks something like this:

.. code-block:: python

    config = dict(
        endpoints={
            "relay_outbound": [
                "tcp://hostA:4001",
            ],
        },
        relay_inbound=[
            "tcp://hostA:2003",
        ],
    )

To confirm that something's not immediately broken, you can go through the
tests of doing ``fedmsg-logger`` and ``fedmsg-tail`` on ``hostA`` again (all
"local").

Copy that relay.py file over to ``hostB`` with ``scp /etc/fedmsg.d/relay.py
hostB:/etc/fedmsg.d/relay.py``

You should now be able to run ``fedmsg-tail`` on ``hostA`` and have it receive
a message from ``fedmsg-logger`` on ``hostB`` and vice versa have a
``fedmsg-tail`` session on ``hostB`` receive a ``fedmsg-logger`` statement from
``hostA``.

The key here is that fedmsg works by having a **shared configuration** that is
distributed to all machines.  ``hostA`` only knows where to publish by reading in
the config and ``hostB`` only knows where to consume by reading in the config.  If
the configs are not the same, then there's going to be a mis-match and your
messages won't arrive... anywhere.

It's a far leap ahead, but you're welcome to browse the `configuration we're
using in production for Fedora Infrastructure
<https://infrastructure.fedoraproject.org/cgit/ansible.git/tree/roles/fedmsg/base>`_.


Store all messages
------------------

And now for a different topic.

We use a tool called `datanommer <https://github.com/fedora-infra/datanommer>`_
to store all the messages that come across the bus in a postgres database.
Using whatever relational database you like should be possible just by
modifying the config.

Setting up postgres
~~~~~~~~~~~~~~~~~~~

Here, set up a postgres database::

    $ sudo dnf install postgresql-server python-psycopg2
    $ postgresql-setup initdb

Edit the ``/var/lib/pgsql/data/pg_hba.conf`` as the user postgres. You might
find a line like this::

  host all all 127.0.0.1/32 ident sameuser
  host all all ::1/128 ident sameuser


Instead of that line, change it to this::

  host all all 127.0.0.1/32 trust
  host all all ::1/128 trust

.. note:: Using ``trust`` is super unsafe long term.  That means that anyone
   with any password will be able to connect locally.  That's fine for our
   little one-box test here, but you'll want to use md5 or kerberos or
   something long term.

Start up postgres::

    $ systemctl start postgresql
    $ systemctl enable postgresql

Create a database user and the db itself for datanommer and friends::

    $ sudo -u postgres createuser -SDRPE datanommer
    $ sudo -u postgres createdb -E utf8 datanommer -O datanommer

Setting up datanommer
~~~~~~~~~~~~~~~~~~~~~

Install it::

    $ sudo dnf install fedmsg-hub python-datanommer-consumer datanommer-commands

Edit the configuration to 1) be enabled, 2) point at your newly created
postgres db.  Edit ``/etc/fedmsg.d/datanommer.py`` and change the whole thing
to look like this::

    config = {
        'datanommer.enabled': True,
        'datanommer.sqlalchemy.url': 'postgresql://datanommer:password@localhost/datanommer',
    }

Run the following command from the ``datanommer-commands`` package to set up
the tables.  It will read in that connection url from
``/etc/fedmsg.d/datanommer.py``::

    $ datanommer-create-db

Start the ``fedmsg-hub`` daemon, which will pick up the datanommer plugin,
which will in turn read in that connection string, start listening for
messages, and store them all in the db.

::

    $ sudo systemctl start fedmsg-hub
    $ sudo systemctl enable fedmsg-hub

You can check ``journalctl --follow`` for logs.

Try testing again with ``fedmsg-logger``.  After publishing a message, you
should see it in the datanommer stats if you run ``datanommer-stats``::

    $ datanommer-stats 
    [2014-03-03 20:34:43][    fedmsg    INFO] logger has 2 entries

Querying datanommer with datagrepper
------------------------------------

You can, of course, query datanommer with SQL yourself (and there's a python
API for directly querying in the ``datanommer.models`` module).  For the rest
here is the HTTP API we have called "datagrepper".  Let's set it up::

    $ sudo dnf install datagrepper mod_wsgi

Add a config file for it in ``/etc/httpd/conf.d/datagrepper.conf`` with these contents::

    LoadModule wsgi_module modules/mod_wsgi.so

    # Static resources for the datagrepper app.
    Alias /datagrepper/css /usr/lib/python2.7/site-packages/datagrepper/static/css

    WSGIDaemonProcess datagrepper user=fedmsg group=fedmsg maximum-requests=50000 display-name=datagrepper processes=8 threads=4 inactivity-timeout=300
    WSGISocketPrefix run/wsgi
    WSGIRestrictStdout Off
    WSGIRestrictSignal Off
    WSGIPythonOptimize 1

    WSGIScriptAlias /datagrepper /usr/share/datagrepper/apache/datagrepper.wsgi

    <Directory /usr/share/datagrepper/>
      WSGIProcessGroup datagrepper
      # XXX - The syntax for this is different for different versions of apache
      Require all granted
    </Directory>

Finally, start up httpd with::

    $ sudo systemctl restart httpd
    $ sudo systemctl enable httpd

And it should just work.  Open a web browser and try to visit
``http://localhost/datagrepper/``.

The whole point of datagrepper is its API, which you might experiment with
using the httpie tool::

    $ sudo dnf install httpie
    $ http get http://localhost/datagrepper/raw/ order==desc

Outro
-----

This document is a work in progress.  Future topics may include selinux and :doc:`crypto`.

Let us know what you'd like to know if it is missing.
