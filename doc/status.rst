FedMsg Status Table
===================

This is a table to keep track of where we are with all the different systems.
There is no information here about *receiving* messages, only sending.

+---------------+-----------+------------+----------+-----------+
| Service       | Dev       |    Stg     |  PKI     |   Prod    |
+===============+===========+============+==========+===========+
| fedmsg-relay  | DONE      |   DONE     | N/A      | DONE      |
+---------------+-----------+------------+----------+-----------+
| fedmsg-irc    | DONE      |   DONE     | N/A      | DONE      |
+---------------+-----------+------------+----------+-----------+
| fedmsg-gateway| DONE      |   DONE     | N/A      | DONE      |
+---------------+-----------+------------+----------+-----------+
| websockets    | DONE      |   DONE     | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| ansible       | DONE      |   N/A      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| askbot        | DONE      |   DONE     | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| autoqa        |           |            |          |           |
+---------------+-----------+------------+----------+-----------+
| badges        | DONE      |   DONE     | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| bodhi         | DONE      |   DONE     | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| bugzilla      | DONE      |   DONE     | DONE     |           |
+---------------+-----------+------------+----------+-----------+
| busmon        | DONE      |   DONE     | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| compose       | DONE      |   N/A      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| comp 2nd arch | DONE      |   N/A      | DONE     | DONE*[4_] |
+---------------+-----------+------------+----------+-----------+
| coprs         | DONE      |   N/A      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| elections     | DONE [1_] |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| fas           | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| fedocal       | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| fedorahosted  | DONE      |   N/A      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| koji          | DONE?     |BLOCKED [3_]| DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| mailman       | DONE      |            |          |           |
+---------------+-----------+------------+----------+-----------+
| meetbot       | DONE      | N/A        | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| nagios        | DONE      |            |          |           |
+---------------+-----------+------------+----------+-----------+
| pastebin      |           |            |          |           |
+---------------+-----------+------------+----------+-----------+
| pkgdb         | DONE      | DONE       | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| planet        | DONE?     |  N/A       | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| scm           | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| sigul         | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| pkgdb2branch  | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| tagger        | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+
| wiki          | DONE      |  DONE      | DONE     | DONE      |
+---------------+-----------+------------+----------+-----------+


.. _1: https://github.com/abadger/fedora-elections-flask/pull/1
.. _2: https://github.com/rossdylan/fuss
.. _3: https://fedorahosted.org/fedora-infrastructure/ticket/3438
.. _4: https://fedorahosted.org/fedora-infrastructure/ticket/3700

Other projects
--------------

There are a number of external tools being built against fedmsg:

 - Luke Macken's `fedmsg-notify <https://github.com/fedora-infra/fedmsg-notify>`_ is
   a dbus daemon that connects the fedmsg bus to users' desktops.
 - Bill Peck's `fedmsg-download <https://github.com/p3ck/fedmsg-download/>`_
   listens to the bus and begins download rawhide and branched composes once
   they are complete for efficient mirroring.
 - Ralph Bean's `datanommer <https://github.com/fedora-infra/datanommer>`_ is a
   storage consumer for fedmsg.  It stores every message it receives in a SQL
   database.
