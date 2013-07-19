# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewose.
#
# Firewose is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

def _get_engine(url, echo):
    return create_engine(url, echo=echo)

def get_engine_session(url, echo=False):
    """
    Given a database URL, returns an SQLAlchemy engine/session
    """
    engine = _get_engine(url, echo=echo)
    session = scoped_session(sessionmaker(bind=engine, autoflush=True))
    return engine, session
