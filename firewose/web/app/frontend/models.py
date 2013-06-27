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


from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, \
    Generator, Sut, Metadata
from sqlalchemy import and_, func, desc

from app import session, app
from filter_search import FilterArgs, create_menu,make_q


### EXCEPTIONS ###

class Http500Error(Exception): pass
class Http404Error(Exception): pass


### MODEL CLASSES ###


def to_dict(elem):
    """
    serializes a SQLAchemy response into a dict
    /!\ backrefs are followed and can do infinite recursion TODO
    """
    if elem is None:
        return None
    elif type(elem) in [int, float, str, unicode, bool, long]:#_string_type]
        return elem
    
    elif isinstance(elem, list):
        return [to_dict(e) for e in elem]
    elif isinstance(elem, tuple): # KeyedTuple (queries with specified columns)
        res = dict()
        elem = elem._asdict()
        for attr_name in elem:
            res[attr_name] = to_dict(elem[attr_name])
        return res
    else:
        res = dict()
        cls = type(elem)
        for attr_name in cls._sa_class_manager.local_attrs:
                attr = getattr(elem, attr_name)
                #if type(attr) in [int, float, str, unicode]:#_string_type]
                #    res[attr_name] = attr
                #else:
                res[attr_name] = to_dict(attr)
        return res


class FHGeneric(object):
    def all(self):
        elem = session.query(self.fh_class).all()
        return to_dict(elem)
    
    def id(self, id):
        try:
            elem = session.query(self.fh_class).filter(
                self.fh_class.id == id).first()
        except:
            raise Http500Error
        
        try:
            id = elem.id # raises error if the element doesn't exist
        except:
            raise Http404Error("This element (%s, %s) doesn't exist."
                               % (self.fh_class.__name__, id))
        return to_dict(elem)

class Generator_app(FHGeneric):
    def __init__(self):
        self.fh_class = Generator

    def all(self):
        elems = session.query(self.fh_class).order_by(Generator.name).all()
        return to_dict(elems)
    
    def unique_by_name(self):
        elems = session.query(Generator.name).distinct().all()
        return to_dict(elems)
    
    def versions(self, name):
        elems = session.query(Generator.version).filter(
            Generator.name == name).all()
        return to_dict(elems)

class Analysis_app(FHGeneric):
    def __init__(self):
        self.fh_class = Analysis

    def all(self):
        elems = session.query(Analysis.id,
                             Generator.name.label("generator_name")).filter(
            and_(Analysis.metadata_id == Metadata.id,
                 Metadata.generator_id == Generator.id)).all()
        return to_dict(elems)

    def id(self, id):
        elem = session.query(Analysis).filter(Analysis.id == id).first()
        elem = to_dict(elem)
        elem['results'] = to_dict(session.query(
                Result.id).filter(Result.analysis_id == id).all())
        return elem

class Sut_app(FHGeneric):
    def __init__(self):
        self.fh_class = Sut
        
    def versions(self, name):
        elems = session.query(Sut).filter(
            Sut.name==name).order_by(Sut.version).all()
        return to_dict(elems)
    
    def name_contains(self, name):
        """ returns the packages whose name contains name """
        elems = session.query(Sut.name).filter(
            Sut.name.contains(name)).distinct().all()
        # we remove 'name' if it's here
        elems = [e for e in elems if e.name != name]
        return to_dict(elems)

class Result_app(FHGeneric):
    def __init__(self):
        self.fh_class = Result
        
    def all(self):
        elems = session.query(Result.id).all()
        return to_dict(elems)
    
    def filter(self, request_args, offset=None):
        """
        returns the results corresponding to the args in request_args,
        along with a drill down menu
        
        offset: number of results (if not set, this value is read in config)
        """
        
        filter_ = FilterArgs(request_args)
        menu = create_menu(filter_)
        clauses = menu.get_clauses()
        
        # TODO: polymorphism?
        q_issue = make_q(session, Issue, clauses)
        q_failure = make_q(session, Failure, clauses)
        q_info = make_q(session, Info, clauses)
        
        # we get the page number and the offset
        try:  page = int(request_args["page"])
        except: page = 1
        
        try: offset = int(request_args["offset"])
        except: offset = offset or app.config["SEARCH_RESULTS_OFFSET"]
        
        # we calculate the range of results
        start = (page - 1) * offset
        end = start + offset
        
        query = q_issue.union(q_failure, q_info).order_by(Result.id)
        results_all = query.all()
        results_all_count = query.count()
        results_sliced = query.slice(start, end).all()

        menu = menu.get_menu_items(
            results=to_dict(results_all),
            limit=app.config["SEARCH_MENU_MAX_NUMBER_OF_ELEMENTS"])
        
        # if only sut.name is in filter, we suggest similar packages:
        try:
            sutname = filter_.get("sut_name")
            if len(filter_.get_all()) == 1:
                packages_suggestions = Sut_app().name_contains(sutname)
            else:
                packages_suggestions = None
        except:
            packages_suggestions = None
            
        return dict(
            results_all_count=results_all_count,
            results_range = (start+1, start+len(results_sliced)),
                    # to avoid 1-10 of 5 results
            page=page,
            offset=offset,
            results=to_dict(results_sliced),
            filter=filter_.get_all(),
            menu=menu,
            packages_suggestions=packages_suggestions)

    def id(self, id, with_metadata=True):
        if not(with_metadata):
            return super(Result_app, self).id(id)
        else:
            elem = session.query(Result, Metadata).filter(and_(
                    Result.id == id,
                    Result.analysis_id == Analysis.id,
                    Analysis.metadata_id == Metadata.id)).first()
            return to_dict(elem)

class Report(object):
    def __init__(self, package_id):
        self.package_id = package_id
        
    def package_infos(self):
        elems = Sut_app().id(self.package_id)
        return elems
    
    def count_per_generator(self):
        elems = (
            session.query(Generator.name,
                          func.count(Result.id).label("count"))
            .join(Sut, Sut.id == self.package_id)
            .join(Metadata, and_(Sut.id == Metadata.sut_id,
                                 Metadata.generator_id==Generator.id))
            .join(Analysis, Analysis.metadata_id == Metadata.id)
            .outerjoin(Result, Result.analysis_id == Analysis.id)
            .group_by(Generator.name)
            .order_by(desc("count"))
            .all())

        return elems
    
    def all(self):
        return dict(
            package_infos = self.package_infos(),
            count_per_generator = to_dict(self.count_per_generator())
            )
