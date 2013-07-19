import re
import argparse
from ftplib import FTP
from email.utils import parseaddr

from firewose.lib.dbutils import get_engine_session
from firewose.lib.firehose_orm import metadata, DebianPackage, DebianMaintainer,\
    DebianPackagePeopleMapping

from sqlalchemy import MetaData, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

url = "ftp.debian.org"
path = "debian/indices/Uploaders"

def ftp_connect(server, user=None, password=None):
    """
    Connects to an FTP server.
    """
    try:
        ftp = FTP(server)#, user, password)
        ftp.login()
    except Exception as e:
        print("Connection error")
    
    return ftp

def ftp_close(ftpo):
    """
    Closes the FTP connection.
    """
    ftpo.quit()

def _proceed_lines(ftpo, path, session, packages, maintainers, mappings):
    def proceed_line(line):
        """
        Splits the line, extracts package name, maintainer name,
        maintainer email, and add this to the session
        """
        try:
            #pack, maint = re.search(r"^([a-z0-9\+\-\.]*)\s.*<(.*)>,?$",
            #                       line.rstrip()).groups()
            try:
                package, maintainer_full = line.rstrip().split(None, 1)
            except Exception as e:
                return
                
            maint_name, maint_email = parseaddr(maintainer_full)
            
            if not packages.get(package):
                packages[package] = DebianPackage(package)
            if not maintainers.get(maint_email):
                maintainers[maint_email] = DebianMaintainer(maint_email,
                                                            maint_name)
            if not mappings.get((package, maint_email)):
                mappings[(package, maint_email)] = DebianPackagePeopleMapping(
                    packages[package], maintainers[maint_email])
                
            global set_p
            global set_m
            set_p.add(package)
            set_m.add(maint_email)
            
            #session.flush()
            #session.merge(mapping)#, load=False)

        except AttributeError:
            pass
    
    global set_p
    global set_m
    set_p = set()
    set_m = set()
    ftpo.retrlines("RETR " + path, proceed_line)
    print("packages: %d" % len(set_p))
    print("maints: %d" % len(set_m))
    
    

def generate_packages_for_people(ftpo, path, session):
    """
    Given an FTP connection and a file path, retrieves the Uploaders file,
    and inserts it in the db.
    """
    
    packages = dict()
    maintainers = dict()
    mappings = dict()
    ftpo = ftp_connect(url)
    _proceed_lines(ftpo, path, session, packages, maintainers, mappings)
    ftp_close(ftpo)
    session.add_all(item for item in mappings.values())
    session.commit()

def clear_debian_tables(session):
    """
    Clear the content of the 3 Debian tables used for packages/people mapping.
    """
    session.execute(metadata.tables["debian_package_people_mapping"].delete())
    session.execute(metadata.tables["debian_packages"].delete())
    session.execute(metadata.tables["debian_maintainers"].delete())
    #session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recreates content in Debian\
    tables, related to packages, maintainers and the link between them. The\
    information comes from a file through ftp.")
                                     
    parser.add_argument("db_url", help="URL of the database")
    parser.add_argument("--verbose", help="outputs SQLAlchemy requests",
                        action="store_true")
    args = parser.parse_args()

    # db cleaning
    engine, session = get_engine_session(args.db_url, echo=args.verbose)
    clear_debian_tables(session)
    
    # ftp connection, db insertion
    #ftpo = ftp_connect(url)
    generate_packages_for_people(path, session)
    #ftp_close(ftpo)
