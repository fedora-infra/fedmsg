===========
Development
===========

Using a virtualenv
------------------

Although you don't strictly *have* to, you should use
`virtualenvwrapper <https://virtualenvwrapper.readthedocs.org/>`_ for isolating
your development environment.  It is to your benefit because you'll be able to
install the latest fedmsg from a git checkout without messing with your system
fedmsg install (if you have one).  The instructions here will assume you are
using that.

You can install it with::

    $ sudo dnf install python-virtualenvwrapper

.. note:: If you decide not to use python-virtualenvwrapper, you can always use
   latest update of fedmsg in fedora.  If you are doing this, simply ignore all
   ``mkvirtualenv`` and ``workon`` commands in these instructions.  You can
   install fedmsg with ``sudo dnf install fedmsg``.

Development Dependencies
------------------------

Get::

    $ sudo dnf install python-virtualenv libffi-devel openssl-devel \
      zeromq-devel gcc

Cloning the Upstream Git Repo
-----------------------------

The source code is on github.  For read-only access, simply::

    $ git clone git://github.com/fedora-infra/fedmsg.git

Of course, you may want to do the usual `fork and then clone
<https://help.github.com/articles/fork-a-repo>`_ pattern if you intend to
submit patches/pull-requests (please do!).

.. note::  If submitting patches, you should check :doc:`contributing` for
   style guidelines.

Setting up your virtualenv
--------------------------

Create a new, empty virtualenv and install all the dependencies from `pypi
<http://pypi.python.org>`_::

    $ cd fedmsg
    $ mkvirtualenv fedmsg
    (fedmsg)$ pip install -e .[all]

.. note::  If the mkvirtualenv command is unavailable try
   ``source /usr/bin/virtualenvwrapper.sh`` on Fedora (if you do not run Fedora
   you might have to adjust the command a little).

.. note::  As discussed in the FAQ, M2Crypto requires the swig command to be
   available in order to build successfully.  It's recommended that you
   install M2Crypto using your system package manager, which can be done with
   ``dnf install m2crypto swig`` on Fedora.

You should also run the tests, just to make sure everything is sane::

    (fedmsg)$ python setup.py test

Try out the shell commands
--------------------------

Having set up your environment in the `Hacking` section above, open up three
terminals.  In each of them, activate your virtualenv with::

  $ workon fedmsg

and in one, type::

  (fedmsg)$ fedmsg-relay

In the second, type::

  (fedmsg)$ fedmsg-tail --really-pretty

In the third, type::

  (fedmsg)$ echo "Hello, world" | fedmsg-logger

And you should see the message appear in the ``fedmsg-tail`` term.

Configuration
-------------

There is a folder in the root of the upstream git checkout named ``fedmsg.d/``.
:mod:`fedmsg.config` will try to read this whenever the fedmsg API is
invoked.  If you're starting a new project like a consumer or a webapp that is
sending fedmsg messages, you'll need to copy the ``fedmsg.d/`` directory to the
root directory of that project.  In :doc:`deployment`, that folder is kept in
``/etc/fedmsg.d/``.

.. note::  Watch out:  if you have a ``/etc/fedmsg.d/`` folder and a local
   ``./fedmsg.d/``, fedmsg will read both.  Global first, and then local.
   Local values will overwrite system-wide ones.

.. note::  The tutorial on `consuming FAS messages from stg
   <http://threebean.org/blog/fedmsg-tutorial-consuming-fas-stg>`_ might be of
   further help.  It was created before these instructions were written.
