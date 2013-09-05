# This file is part of fedmsg
# Copyright (C) 2013 Simon Chopin <chopin.simon@gmail.com>
#
# fedmsg is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# fedmsg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with fedmsg; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#
# Authors:  Simon Chopin <chopin.simon@gmail.com>
#

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

from sqlalchemy import Column, Integer, String, Text, DateTime, or_
from sqlalchemy.orm import sessionmaker

from datetime import datetime
import json


class SqlMessage(Base):
    # This should probably be customizeable?
    __tablename__ = "fedmsg_messages"

    seq_id = Column(Integer, primary_key=True)
    uuid = Column(String(36))
    topic = Column(String)
    timestamp = Column(DateTime)
    # The raw message, including the metadata (signature, topic, etc)
    msg = Column(Text)


class SqlStore(object):
    def __init__(self, engine):
        self.engine = engine
        self.session_class = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)

    def add(self, msg):
        session = self.session_class()
        msg_object = SqlMessage(
            uuid=msg['msg_id'],
            timestamp=datetime.fromtimestamp(msg['timestamp']),
            topic=msg['topic'],
            # We still have to add the seq_id field
            msg=""
        )
        session.add(msg_object)
        session.commit()
        msg['seq_id'] = msg_object.seq_id
        msg_object.msg = json.dumps(msg)
        session.commit()
        session.close()
        return msg

    def _query_seq_ids(self, arg):
        return SqlMessage.seq_id.in_(arg)

    def _query_seq_id(self, arg):
        return SqlMessage.seq_id == arg

    def _query_seq_id_range(self, arg):
        try:
            sid_beg, sid_end = arg
        except (TypeError, ValueError):
            raise ValueError('Ill-format "sed_id_range" field')
        return SqlMessage.sed_id.between(sid_beg, sid_end)

    def _query_msg_ids(self, arg):
        return SqlMessage.uuid.in_(arg)

    def _query_msg_id(self, arg):
        return SqlMessage.uuid == arg

    def _query_time(self, arg):
        try:
            time_beg, time_end = arg
        except (TypeError, ValueError):
            raise ValueError('Ill-format "time" field')
        return SqlMessage.timestamp.between(
            datetime.fromtimestamp(time_beg),
            datetime.fromtimestamp(time_end)
        )

    def get(self, query):
        predicates = []

        for key, value in query.iteritems():
            fn = getattr(self, '_query_{0}'.format(key), None)
            if not fn:
                raise ValueError('Unsupported field: "key"')
            try:
                predicates.append(fn(value))
            except ValueError:
                raise
            except Exception:
                raise ValueError('Something went wrong when processing '
                                 'the field "{0}"'.format(key))

        session = self.session_class()

        ret = [json.loads(m[0])
               for m in session.query(SqlMessage.msg)
               .filter(or_(*predicates)).all()]
        session.close()
        if len(ret) == 0:
            raise ValueError('There was no match for the given query')
        return ret
