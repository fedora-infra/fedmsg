Replay
======

.. automodule:: fedmsg.replay
    :members:
    :undoc-members:
    :show-inheritance:

Replay queries
--------------

Currently, a query is the union of multiple criteria. It means that the more criteria you
add, the bigger the result set should become. The following criteria are supported:

.. glossary::

    seq_ids
        ``list`` - A list of integers, matching the seq_id attributes of the messages.
        It should return at most as many messages as the length of the list, assuming
        no duplicate. Supported by ``SqlStore``.

    seq_id
        ``int`` - A single integer matching the seq_id attribute of the messages.
        Should return a single message. It is intended as a shorthand for singleton
        ``seq_ids`` queries. Supported by ``SqlStore``.

    seq_id_range
        ``tuple`` - A couple of integers defining a range of seq_id to check.
        Supported by ``SqlStore``

    msg_ids
        ``list`` - a list of UUIDs matching the msg_id attribute of the messages.
        Supported by ``SqlStore``.

    msg_id
        ``uuid`` - A single UUID for the msg_id attribute. Supported by ``SqlStore``.

    time
        ``tuple`` - Couple of timestamps. It will return all messages emitted inbetween.
        Supported by ``SqlStore``
