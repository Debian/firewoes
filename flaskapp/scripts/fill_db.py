# Reads Firehose-related XML through standard input and injects it to a DB

# Note: we have to emulate files with cStringIO, because
# firehose.model.Analysis.from_xml method only takes a file as input

import os, sys
from cStringIO import StringIO
import argparse # TODO --sqlite, --db, --drop, ...

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 

from modules.ormapping import metadata

import firehose_noslots as fhm
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

if __name__ == "__main__":
    try:
        url = sys.argv[1]
    except:
        print("usage: python scripts/fill_db.py db_url < some_xml")
        sys.exit()
    
    #url = os.path.abspath(url)
    #if not os.path.exists(url):
    #    print("warning: the database doesn't exist yet")
    
    #url = "sqlite:///" + url
    engine, session = get_engine_session(url, echo=True)
    
    metadata.drop_all(bind=engine) # cleans the table (for debugging)
    metadata.create_all(bind=engine)
    
    # we feed an ExtractAnalysis object with the standard input:
    target = ExtractAnalysis(session)
    parser = ET.XMLParser(target=target)
    
    parser.feed("<xmlroot>") # to allow multiple analyses to be parsed
    for line in sys.stdin.readlines():
        # TODO better (xml decl. are now inside <xmlroot>, which is incorrect):
        if not "<?xml" in line:
            target.addline(line)
            parser.feed(line.rstrip())
    parser.feed("</xmlroot>")
    parser.close()
