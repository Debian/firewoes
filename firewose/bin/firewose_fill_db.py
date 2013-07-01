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


# Reads a Firehose-related XML file and injects it to a DB

import os, sys
import argparse

from firewose.lib.firehose_unique import get_fh_unique

import firewose.lib.firehose_orm as fhm
metadata = fhm.metadata

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def _get_engine(url, echo):
    return create_engine(url, echo=echo)

def get_engine_session(url, echo=False):
    """
    Given a database URL, returns an SQLAlchemy engine/session
    """
    engine = _get_engine(url, echo=echo)
    Session = sessionmaker(bind=engine, autoflush=True)
    session = Session()
    return engine, session

def insert_analysis(session, xml_file):
    """
    Given a file object and a session, creates a Firehose Analysis() object
    and inserts it to the db linked to session
    """
    analysis = fhm.Analysis.from_xml(xml_file)
    # unicity:
    try:
        analysis = get_fh_unique(session, analysis)
    except Exception as e:
        print(e)
        import sys; sys.exit()

    session.merge(analysis)
    session.commit()
    
def read_and_create(url, xml_files, drop=False, echo=False):
    engine, session = get_engine_session(url, echo=echo)
    
    if drop:
        metadata.drop_all(bind=engine) # cleans the table (for debugging)
        metadata.create_all(bind=engine)
    
    for file_ in xml_files:
        try:
            insert_analysis(session, file_)
        except Exception as e:
            print("Error in file %s, it maybe contains "
                  "invalid characters" % file_)
            print(e)
            

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Reads XML from standard\
    input and adds the Firehose objects into the specified database")
    parser.add_argument("db_url", help="URL of the database")
    parser.add_argument("xml_file", help="Path of the XML file", nargs="+")
    parser.add_argument("--drop", help="drops the database before filling",
                        action="store_true")
    parser.add_argument("--verbose", help="outputs SQLAlchemy requests",
                        action="store_true")
    args = parser.parse_args()
    
    read_and_create(args.db_url, args.xml_file, drop=args.drop, echo=args.verbose)
    
