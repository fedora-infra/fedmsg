fedmsg -- Fedora Messaging Client API
=====================================

.. split here

Utilities used around Fedora Infrastructure to send and receive messages.
Please see ``doc/`` for more info.

Hacking
-------

Install the dependencies.  (This list is a work in progress.
The ``python-*`` packages from http://pypi.python.org/ are not listed
for now, since they are ever-evolving.)::

 $ sudo yum install python-virtualenv openssl-devel

Get the source::

  $ git clone git://github.com/ralphbean/fedmsg.git
  $ cd fedmsg

Make a virtualenv::

  $ virtualenv fedmsg-env
  $ source fedmsg-env/bin/activate
  (fedmsg-env)$

Pull down pypi dependencies::

  (fedmsg-env)$ python setup.py develop

Try out the shell commands
--------------------------

Having set up your environment in the `Hacking` section above, open up three
terminals.  In each of them, activate your virtualenv with::

  $ source fedmsg-env/bin/activate

and in one, type::

  (fedmsg-env)$ fedmsg-relay

In the second, type::

  (fedmsg-env)$ fedmsg-tail --pretty

In the third, type::

  (fedmsg-env)$ echo "Hello, world" | fedmsg-logger

And you should see the message appear in the ``fedmsg-tail`` term.
