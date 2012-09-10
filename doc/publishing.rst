Python API:  Emitting Messages
==============================

TODO - move to autodoc for fedmsg.publish

Here's a real dummy test::

    >>> import fedmsg
    >>> fedmsg.publish(topic='testing', modname='test', msg={
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
    >>> fedmsg.publish(topic='tag.update', msg={
    ...     'user': user,
    ...     'tag': tag,
    ... })

Note that the `tag` and `user` objects are SQLAlchemy objects defined by
tagger.  They both have ``.__json__()`` methods which ``.publish``
uses to convert both objects to stringified JSON for you.

``fedmsg`` has also guessed the module name (``modname``) of it's caller and
inserted it into the topic for you.  The code from which we stole the above
snippet lives in ``fedoratagger.controllers.root``.  ``fedmsg`` figured that
out and stripped it down to just ``fedoratagger`` for the final topic of
``org.fedoraproject.{dev,stg,prod}.fedoratagger.tag.update``.

----

You could also use the ``fedmsg-logger`` from a shell script like so::

    $ echo "Hello, world." | fedmsg-logger --topic testing
    $ echo '{"foo": "bar"}' | fedmsg-logger --json-input

