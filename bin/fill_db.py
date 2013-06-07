# Reads a Firehose-related XML file and injects it to a DB

import os, sys
import argparse

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, parentdir) 

from lib.firehose_unique import get_fh_unique
#from lib.firehose_orm import metadata
import lib.firehose_orm as fhm
metadata = fhm.metadata

#import firehose_noslots as fhm
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
    analysis = get_fh_unique(session, analysis)
    
    session.merge(analysis)
    session.commit()
    
def read_and_create(url, xml_file, drop=False, echo=False):
    engine, session = get_engine_session(url, echo=echo)
    
    if drop:
        metadata.drop_all(bind=engine) # cleans the table (for debugging)
        metadata.create_all(bind=engine)
    
    for file_ in xml_file:
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
    