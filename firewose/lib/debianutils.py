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


# to generate links safely
try:
    from werkzeug.urls import url_quote
except ImportError:
    from urlparse import quote as url_quote

from sqlalchemy.ext.declarative import declarative_base

from debian.debian_support import version_compare

from firewose.lib.orm import *
from firewose.web.app import session
from sqlalchemy import and_

"""
This module is intented to generate links to point on code listing,
e.g. the one used with Debian on http://sources.debian.net
"""

def get_source_url(url,
                   package, version, release, path,
                   start_line, end_line=None,
                   message=None):
    """
    Creates an url for source code visualisation.
    
    Args:
    url_prefix: the base url
         e.g.: http://sources.debian.net/src/{package}/{version}/{path}?...
    package: the package name, e.g. python-ethtool
    version: the package version
    release: the package release
    start_line: the first line to highlight and the one pointed by {anchor}
    end_line: if provided, the last line to highlight
    message: if provided, the message (e.g. sources.d.n supports this)
    """
    url = (url
           .replace("{package}", url_quote(package))
           .replace("{version}", url_quote(version))
           .replace("{release}", url_quote(release))
           .replace("{path}", url_quote(path))
           .replace("{anchor}", str(start_line))
           )
    
    if end_line is not None:
        lines_range = str(start_line) + ":" + str(end_line)
    else:
        lines_range = str(start_line)
    url = url.replace("{lines_range}", lines_range)
        
    if message is not None:
        url = url.replace("{message}", "%d:error:%s" % (start_line,
                                                        url_quote(message)))
    else:
        url = url.replace("{message}", "") # we don't want {message} of course
    
    return url
    
def packages_for_person(session, login):
    """
    Returns a list of package names, whose responsible is login.
    """
    def base_query():
        return (session.query(DebianPackage.name)
                .filter(and_(
                    DebianPackage.name == \
                        DebianPackagePeopleMapping.debian_package_name)))
    
    if "@" in login: # email
        res = (base_query().filter(
                DebianPackagePeopleMapping.debian_maintainer_email == login)
               .all())
    else: # login or full name
        res = (base_query().filter(
                DebianPackagePeopleMapping.debian_maintainer_email == \
                    DebianMaintainer.email,
                DebianMaintainer.name == login)
               .all())
        if len(res) == 0: # login
            login = login + "@debian.org"
            res = (base_query().filter(
                    DebianPackagePeopleMapping.debian_maintainer_email == login)
               .all())
    return res

def email_for_person(person):
    """
    Given a login, a full name, or an email, returns the corresponding email.
    """
    if "@" in person:
        return person
    res = (session.query(DebianMaintainer)
           .filter(DebianMaintainer.name == person)
           .first())
    if res:
        return res.email
    
    res = (session.query(DebianMaintainer)
           .filter(DebianMaintainer.email == person + "@debian.org")
           .first())
    if res:
        return res.email
    
    return None

###################################################
### Debian specific tables, objects and mappers ###
###################################################

Base = declarative_base()

class DebianPackage(Base):
    __tablename__ = "debian_packages"
    
    name = Column(String, primary_key=True, index=True)
    mappings = relationship("DebianPackagePeopleMapping", backref="package")
    
    def __init__(self, name):
        self.name = name

class DebianMaintainer(Base):
    __tablename__ = "debian_maintainers"
    
    email = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    mappings = relationship("DebianPackagePeopleMapping", backref="maintainer")
    
    def __init__(self, email, name):
        self.email = email
        self.name = name

class DebianPackagePeopleMapping(Base):
    __tablename__ = "debian_package_people_mapping"
    
    package_name = Column(
        String, ForeignKey('debian_packages.name'), primary_key=True)
    maintainer_email = Column(
        String, ForeignKey('debian_maintainers.email'),
        primary_key=True, index=True)
    
    def __init__(self, package_name, maintainer_email):
        self.package = package_name
        self.maintainer = maintainer_email
