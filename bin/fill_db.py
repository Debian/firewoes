# Reads Firehose-related XML through standard input and injects it to a DB

# Note: we have to emulate files with cStringIO, because
# firehose.model.Analysis.from_xml method only takes a file as input

import os, sys
from cStringIO import StringIO
import argparse

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, parentdir) 

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

def insert_analysis(session, file_analysis):
    """
    Given a file object and a session, creates a Firehose Analysis() object
    and inserts it to the db linked to session
    """
    analysis = fhm.Analysis.from_xml(file_analysis)
    session.merge(analysis)
    session.commit()
    
import xml.etree.ElementTree as ET

class ExtractAnalysis(object):
    """
    This is used to extract analyses from standard input.
    xmlbuffer stores 1 analysis and when the <analysis> subtree is reached,
    the db insertion process is thrown.
    """
    def __init__(self, session, root="analysis"):
        self.xmlbuffer = StringIO()
        self.session = session
        self.root = root
    def addline(self, linestr):
        """ adds a line to the buffer """
        self.xmlbuffer.write(linestr)
    def start(self, tag, attrib):
        """ when an opening xml tag is found """
        #print("start "+tag)
    def end(self, tag):
        """ when a closing xml tag is found """
        #print("end "+tag)
        if tag == self.root: # end of analysis
            self.xmlbuffer.seek(0)
            insert_analysis(self.session, self.xmlbuffer) # TODO: threading
            self.xmlbuffer.close
            self.xmlbuffer = StringIO()
    def data(self, data):
        """ when data between tags is found """
    def close(self):
        self.xmlbuffer.close()

def parse_and_create(url, streamobj, drop=False, echo=False):
    engine, session = get_engine_session(url, echo=echo)
    
    if drop:
        metadata.drop_all(bind=engine) # cleans the table (for debugging)
        metadata.create_all(bind=engine)
    
    # we feed an ExtractAnalysis object with the standard input:
    target = ExtractAnalysis(session)
    parser = ET.XMLParser(target=target)
    
    parser.feed("<xmlroot>") # to allow multiple analyses to be parsed
    
    for line in streamobj.readlines():
        # TODO better (xml decl. are now inside <xmlroot>, which is incorrect):
        if not "<?xml" in line:
            target.addline(line)
            try:
                parser.feed(line.rstrip())
            except:
                print("HERE: %s" % line.rstrip())
                sys.exit()
    parser.feed("</xmlroot>")
    parser.close()    

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Reads XML from standard\
    input and adds the Firehose objects into the specified database")
    parser.add_argument("db_url", help="URL of the database")
    parser.add_argument("--drop", help="drops the database before filling",
                        action="store_true")
    parser.add_argument("--verbose", help="outputs SQLAlchemy requests",
                        action="store_true")
    args = parser.parse_args()
    
    parse_and_create(args.db_url, sys.stdin, drop=args.drop, echo=args.verbose)
    
