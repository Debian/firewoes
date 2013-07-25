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
                    self.clauses += new_filter.get_clauses()
    
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
        res = dict(active=self.active,
                   name=self.__class__.__name__)
        
        if not self.active:
            res["items"] = self.get_items(session, clauses=clauses)
        else:
            res["value"] = self.value
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

class FilterFirehoseAttribute(Filter):
    def is_relevant(self, active_keys=None):
        for dep in self._dependencies:
            if dep not in active_keys:
                return False
        return True
    
    def joins(self, query):
        raise NotImplementedError
    
    def group_by(self, session, attribute, clauses=None):
        query = session.query(attribute.label("value"),
                              func.count(Result.id).label("count"))
        
        # here we describe the path from 'attribute' to Result,
        # in order for SQLA to create the correct joins
        # it would be great to can put all things in same query, though
        
        if attribute in [Generator.name, Generator.version]:
            query = (query.join(Metadata, Metadata.generator_id==Generator.id)
                     .join(Sut, Metadata.sut_id==Sut.id)
                     .join(Analysis, Analysis.metadata_id == Metadata.id)
                     .join(Result, Result.analysis_id == Analysis.id)
                     .join(Location, Result.location_id==Location.id)
                     .join(Function, Location.function_id==Function.id)
                     .join(File, Location.file_id==File.id))
        
        elif attribute in [Sut.type, Sut.name, Sut.version, Sut.release,
                           Sut.buildarch]:
            query = (query.join(Metadata, Metadata.sut_id==Sut.id)
                     .join(Generator, Metadata.generator_id==Generator.id)
                     .join(Analysis, Analysis.metadata_id == Metadata.id)
                     .join(Result, Result.analysis_id == Analysis.id)
                     .join(Location, Result.location_id==Location.id)
                     .join(Function, Location.function_id==Function.id)
                     .join(File, Location.file_id==File.id))
        
        elif attribute in [File.givenpath]:
            query = (query.join(Location, Location.file_id==File.id)
                     .join(Function, Location.function_id==Function.id)
                     .join(Result, Result.location_id==Location.id)
                     .join(Analysis, Result.analysis_id == Analysis.id)
                     .join(Metadata, Analysis.metadata_id==Metadata.id)
                     .join(Sut, Metadata.sut_id==Sut.id)
                     .join(Generator, Metadata.generator_id==Generator.id)
                     )
        
        elif attribute in [Function.name]:
            query = (query.join(Location, Location.function_id==Function.id)
                     .join(File, Location.file_id==File.id)
                     .join(Result, Result.location_id==Location.id)
                     .join(Analysis, Result.analysis_id == Analysis.id)
                     .join(Metadata, Analysis.metadata_id==Metadata.id)
                     .join(Sut, Metadata.sut_id==Sut.id)
                     .join(Generator, Metadata.generator_id==Generator.id)
                     )
        
        
        if clauses is not None:
            query = query.filter(and_(*clauses))
        query = (query
               .group_by(attribute)
               .order_by(desc("count"))
               .all())
        return query

##################################################
# real world filters:
##################################################

### GENERATOR ###

# class FilterGenerator(FilterFirehoseAttribute):
#     def get_items_generator(self, session, attribute, clauses=None):
#         res = (session.query(attribute,
#                              func.count(Result.id).label("count"))
#                .join(Metadata, Metadata.generator_id==Generator.id)
#                .join(Sut, Metadata.sut_id==Sut.id)
#                .join(Analysis, Analysis.metadata_id == Metadata.id)
#                .join(Result, Result.analysis_id == Analysis.id)
#                )
#         if clauses is not None:
#             res = res.filter(and_(*clauses))
#         res = (res
#                .group_by(attribute)
#                .order_by(desc("count"))
#                .all())
#         return res

class FilterGeneratorName(FilterFirehoseAttribute):
    _dependencies = []
    
    def get_clauses(self):
        return [(Generator.name == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_generator(session, Generator.name, clauses=clauses)
        res = self.group_by(session, Generator.name, clauses=clauses)
        return to_dict(res)
    
    # def joins(self, query):
    #     return (query.join(Metadata, Metadata.generator_id==Generator.id)
    #             .join(Sut, Metadata.sut_id==Sut.id)
    #             .join(Analysis, Analysis.metadata_id == Metadata.id)
    #             .join(Result, Result.analysis_id == Analysis.id)

class FilterGeneratorVersion(FilterFirehoseAttribute):
    _dependencies = ["generator_name"]
    
    def get_clauses(self):
        return [(Generator.version == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_generator(session, Generator.version,
        #                               clauses=clauses)
        res = self.group_by(session, Generator.version, clauses=clauses)
        return to_dict(res)

### SUT ###

# class FilterSut(FilterFirehoseAttribute):
#     def get_items_sut(self, session, attribute, clauses=None):
#         res = (session.query(attribute,
#                              func.count(Result.id).label("count"))
#                .join(Metadata, Metadata.sut_id==Sut.id)
#                .join(Generator, Metadata.generator_id==Generator.id)
#                .join(Analysis, Analysis.metadata_id == Metadata.id)
#                .join(Result, Result.analysis_id == Analysis.id)
#                )
#         if clauses is not None:
#             res = res.filter(and_(*clauses))
#         res = (res
#                .group_by(attribute)
#                .order_by(desc("count"))
#                .all())
#         return res

class FilterSutType(FilterFirehoseAttribute):
    _dependencies = []
    
    def get_clauses(self):
        return [(Sut.type == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_sut(session, Sut.type, clauses=clauses)
        res = self.group_by(session, Sut.type, clauses=clauses)
        return to_dict(res)


class FilterSutName(FilterFirehoseAttribute):
    _dependencies = []
    
    def get_clauses(self):
        return [(Sut.name == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_sut(session, Sut.name, clauses=clauses)
        res = self.group_by(session, Sut.name, clauses=clauses)
        return to_dict(res)

class FilterSutVersion(FilterFirehoseAttribute):
    _dependencies = ["sut_name"]
    
    def get_clauses(self):
        return [(Sut.version == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_sut(session, Sut.version, clauses=clauses)
        res = self.group_by(session, Sut.version, clauses=clauses)
        return to_dict(res)

class FilterSutRelease(FilterFirehoseAttribute):
    _dependencies = ["sut_name"]
    
    def get_clauses(self):
        return [(Sut.release == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_sut(session, Sut.release, clauses=clauses)
        res = self.group_by(session, Sut.release, clauses=clauses)
        return to_dict(res)

class FilterSutBuildarch(FilterFirehoseAttribute):
    _dependencies = ["sut_name"]
    
    def get_clauses(self):
        return [(Sut.buildarch == self.value)]
    
    def get_items(self, session, clauses=None):
        #res = self.get_items_sut(session, Sut.buildarch, clauses=clauses)
        res = self.group_by(session, Sut.buildarch, clauses=clauses)
        return to_dict(res)

### LOCATION ###

class FilterLocationFile(FilterFirehoseAttribute):
    _dependencies = ["sut_name"]
    
    def get_clauses(self):
        return [(File.givenpath == self.value),
                (Location.file_id==File.id)]
    
    def get_items(self, session, clauses=None):
        res = self.group_by(session, File.givenpath, clauses=clauses)
        return to_dict(res)    

class FilterLocationFunction(FilterFirehoseAttribute):
    _dependencies = ["sut_name", "location_file"]
    
    def get_clauses(self):
        return [(Function.name == self.value),
                (Location.function_id == Function.id)]
    
    def get_items(self, session, clauses=None):
        res = self.group_by(session, Function.name, clauses=clauses)
        return to_dict(res)    
    

all_filters = [
    ("generator_name", FilterGeneratorName),
    ("generator_version", FilterGeneratorVersion),
    ("sut_type", FilterSutType),
    ("sut_name", FilterSutName),
    ("sut_version", FilterSutVersion),
    ("sut_release", FilterSutRelease),
    ("sut_buildarch", FilterSutBuildarch),
    ("location_file", FilterLocationFile),
    ("location_function", FilterLocationFunction),
    ]



if __name__ == "__main__":
    menu = Menu(dict(generator_name="coccinelle"))
    print(menu)
