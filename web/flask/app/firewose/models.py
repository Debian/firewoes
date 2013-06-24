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


from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, Generator, Sut, Metadata, Message, Location, File, Point, Range, Function
from sqlalchemy import and_

from app import session, app
from filter_search import get_precise_menu, get_filter_clauses_from_clean_args,\
    make_q


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
    elif type(elem) in [int, float, str, unicode, bool]:#_string_type]
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
            raise Http404Error("This element (%s, %i) doesn't exist."
                               % (self.fh_class.__name__, id))
        return to_dict(elem)

class Generator_app(FHGeneric):
    def __init__(self):
        self.fh_class = Generator

    def all(self):
        elem = session.query(self.fh_class).order_by(Generator.name).all()
        return to_dict(elem)
    
    def unique_by_name(self):
        elem = session.query(Generator.name).distinct().all()
        return to_dict(elem)
    
    def versions(self, name):
        elem = session.query(Generator.version).filter(
            Generator.name == name).all()
        return to_dict(elem)

class Analysis_app(FHGeneric):
    def __init__(self):
        self.fh_class = Analysis

    def all(self):
        elem = session.query(Analysis.id,
                             Generator.name.label("generator_name")).filter(
            and_(Analysis.metadata_id == Metadata.id,
                 Metadata.generator_id == Generator.id)).all()
        return to_dict(elem)

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
        elem = session.query(Sut.version).filter(
            Sut.name==name).order_by(Sut.version).all()
        return to_dict(elem)

class Result_app(FHGeneric):
    def __init__(self):
        self.fh_class = Result
        
    def all(self):
        elem = session.query(Result.id).all()
        return to_dict(elem)
    
   
    
    def filter(self, request_args):      
        if "q" in request_args.keys():
            # /search?q=sut.name:hello%20sut.version:blabla...
            clean_args = get_clean_args_from_query(request_args["q"])
        else:
            # /search?sut.name=hello&sut.version=blabla...
            clean_args = [(name, value) for name, value
                          in request_args.iteritems()]

        filter_, clauses = get_filter_clauses_from_clean_args(clean_args)
        
        # TODO: polymorphism?
        q_issue = make_q(session, Issue, clauses)
        q_failure = make_q(session, Failure, clauses)
        q_info = make_q(session, Info, clauses)
        
        # we get the page number and the offset
        try:  page = int(request_args["page"])
        except: page = 1
        
        try: offset = int(request_args["offset"])
        except: offset = app.config["SEARCH_RESULTS_OFFSET"]
        
        # we calculate the range of results
        start = (page - 1) * offset
        end = start + offset
        
        query = q_issue.union(q_failure, q_info).order_by(Result.id)
        results_all = query.all()
        results_all_count = query.count()
        results_sliced = query.slice(start, end).all()
        
        precise_menu = get_precise_menu(
            results_all, filter_,
            max_number_of_elements=app.config[
                "SEARCH_MENU_MAX_NUMBER_OF_ELEMENTS"])

        return dict(
            results_all_count=results_all_count,
            results_range = (start+1, start+len(results_sliced)),
                    # to avoid 1-10 of 5 results
            page=page,
            offset=offset,
            results=to_dict(results_sliced),
            filter=filter_,
            precise_menu=precise_menu)

    def id(self, id, with_metadata=True):
        if not(with_metadata):
            return super(Result_app, self).id(id)
        else:
            elem = session.query(Result, Metadata).filter(and_(
                    Result.id == id,
                    Result.analysis_id == Analysis.id,
                    Analysis.metadata_id == Metadata.id)).first()
            return to_dict(elem)
