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


from models import to_dict

from firewose.lib.firehose_orm import Analysis, Issue, Failure, Info, Result, \
    Generator, Sut, Metadata, Message, Location, File, Point, Range, Function

from sqlalchemy import func, desc, and_

class Menu(object):
    """
    A menu is a set of active and inactive filters.
    It permits to obtain a drill-down menu, as long as an SQLAlchemy
    filter to query the results.
    """
    def __init__(self, active_filters_dict):
        """
        Creates a menu.
        The active_filter_dict contains the already activated filters,
        in the form name=value, e.g. generator_name="coccinelle".
        """
        self.filters = []
        self.clauses = []
        
        # we create the filters:
        for filter_ in all_filters:
            if filter_[0] in active_filters_dict.keys(): # it's an active filter
                new_filter = filter_[1](value=active_filters_dict[filter_[0]],
                                        active=True)
            else: # it's an inactive one
                new_filter = filter_[1](active=False)
            # avoids adding non-relevant filters regarding the context:
            if new_filter.is_relevant(active_keys=active_filters_dict.keys()):
                self.filters.append(new_filter)
                if new_filter.is_active():
                    self.clauses.append(new_filter.get_clauses())
    
    def filter_sqla_query(self, query):
        """
        Filters the query by all active filters, and returns a new
        SQLAlchely query.
        """
        # for filter_ in self.filters:
        #     if filter_.is_active():
        #         query = filter_.sqla_filter(query)
        query = query.filter(and_(*self.clauses))
        return query
    
    def get(self, session):
        """
        Returns the menu in form of a list of filters.
        Needs a SQLAlchemy session for the filters, in their items generation.
        """
        return [filter_.get(session, clauses=self.clauses)
                for filter_ in self.filters]
    
    def __repr__(self):
        string = "MENU:\n"
        for filter_ in self.filters:
            string += "  " + filter_.__repr__() + "\n"
        return string

class Filter(object):
    def __init__(self, value=None, active=False):
        """
        Creates a new filter.
        value is its value in case active=True
        """
        self.value = value
        self.active = active
        if not active:
            self.items = []
    
    def get_clauses(self):
        """
        Returns the SQLAlchemy clauses for this filter.
        """
        # query.filter/filter_by/...
        return query
    
    def get_items(self, session, clauses=None):
        """
        Returns the subitems of the menu (only for inactive filters).
        """
        return None
    
    def get(self, session, clauses=None):
        """
        Returns the filter with its attributes.
        """
        res = dict(active=self.active, name=self.__class__.__name__)
        if not self.active:
            res["items"] = self.get_items(session, clauses=clauses)
        return res
    
    def group_by_firehose(self, session, firehose_attr, clauses=None):
        """
        Given a session and a firehose attribute, returns the objects obtained
        after a group_by and a results count.
        """
        res = (
            session.query(firehose_attr,
                          func.count(Result.id).label("count"))
            .join(Metadata, Metadata.generator_id==Generator.id)
            .join(Analysis, Analysis.metadata_id == Metadata.id)
            .outerjoin(Result, Result.analysis_id == Analysis.id)
            )
        if clauses is not None:
            res = res.filter(and_(*clauses))
        res = (res
               .group_by(firehose_attr)
               .order_by(desc("count"))
               .all())
        
        return res
    
    def is_relevant(self, active_keys=None):
        """
        Returns True if the filter must be used in this context.
        For filters which implement this, should return False if a
        dependency is not satisfied (e.g. generator_version depends on
        generator_name)
        """
        return True
    
    def is_active(self):
        return self.active
    
    def __repr__(self):
        string = self.__class__.__name__ + ":\n"
        string += "    active: " + str(self.active) + "\n"
        if not self.active:
            string += "    items: "
            for item in self.items:
                string += item
            
        return string


class FilterGeneratorName(Filter):
    def get_clauses(self):
        return (Generator.name == self.value)
    
    def get_items(self, session, clauses=None):
        res = self.group_by_firehose(session, Generator.name, clauses=clauses)
        return to_dict(res)

class FilterGeneratorVersion(Filter):
    def is_relevant(self, active_keys=None):
        if isinstance(active_keys, list):
            if "generator_name" in active_keys:
                return True
        return False
    
    def get_clauses(self):
        return (Generator.version == self.value)
    
    def get_items(self, session, clauses=None):
        res = self.group_by_firehose(session, Generator.version, clauses=clauses)
        return to_dict(res)



all_filters = [
    ("generator_name", FilterGeneratorName),
    ("generator_version", FilterGeneratorVersion),
    ]



if __name__ == "__main__":
    menu = Menu(dict(generator_name="coccinelle"))
    print(menu)
