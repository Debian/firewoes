# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewoes.
#
# Firewoes is free software: you can redistribute it and/or modify it under
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

import firewoes.lib.orm as fhm
from firewoes.lib.hash import idify, uniquify
from firewoes.lib.dbutils import get_engine_session

from xml.etree.ElementTree import ParseError as XmlParseError

metadata = fhm.metadata


def insert_analysis(session, xml_file):
    """
    Given a file object and a session, creates a Firehose Analysis() object
    and inserts it to the db linked to session
    """
    try:
        analysis = fhm.Analysis.from_xml(xml_file)
    except XmlParseError:
        return # if file is empty for example
    except Exception as e:
        print("ERROR while parsing xml: %s" % e)
        return
    
    #idify:
    try:
        (analysis, analysishash) = idify(analysis)
    except Exception as e:
        print("ERROR while idify Analysis: %s" % e)
        import sys; sys.exit()
    
    # unicity:
    try:
        analysis = uniquify(session, analysis)
    except Exception as e:
        print("ERROR while uniquify Analysis: %s" % e)
        import sys; sys.exit()

    session.merge(analysis)
    session.commit()
    
def read_and_create(url, xml_files, drop=False, echo=False):
    engine, session = get_engine_session(url, echo=echo)
    
    if drop:
        metadata.drop_all(bind=engine) # cleans the table (for debugging)
        metadata.create_all(bind=engine)
    
    number_of_files = len(xml_files)
    for (counter, file_) in enumerate(xml_files):
        try:
            insert_analysis(session, file_)
        except Exception as e:
            print("Error in file %s" % file_)
            print(e)
        
        # % counter:
        sys.stdout.write(str(int(float(counter + 1)
                                 / float(number_of_files) * 100)))
        sys.stdout.write(" %")
        sys.stdout.write("\r")
        sys.stdout.flush()
    
    session.remove()

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
    
