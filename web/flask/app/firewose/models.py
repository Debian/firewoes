from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, Generator, Sut, Metadata, Message, Location, File, Point, Range
from sqlalchemy import and_

from app import session, app


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
        def get_clean_args_from_query(query):
            """ when all args are in q, this extracts them """
            # query string preprocessing
            query = query.replace(",", " ")
            query = query.replace(";", " ")
            
            args = query.split()
            clean_args = []

            for arg in args:
                try:
                    name, value = arg.split(":")
                    clean_args.append((name, value))
                except: pass

            return clean_args
            
        def get_filter_clauses_from_clean_args(args):
            """
            returns the filter and the clauses correponding to
            the given args
            """
            filter_ = dict()
            clauses = []
            for (name, value) in args:
                if value != "":
                    if name == "sut.name":
                        clauses.append(Sut.name == value)
                        filter_["sut.name"] = value
                    elif name == "sut.version":
                        clauses.append(Sut.version == value)
                        filter_["sut.version"] = value
                    elif name == "generator.name":
                        clauses.append(Generator.name == value)
                        clauses.append(Metadata.generator_id == Generator.id)
                        filter_["generator.name"] = value
            return filter_, clauses

        
        def make_q(class_, clauses):
            """ returns a request for a result (issue/failure/info) """
            return (session.query(
                    class_.id, class_.type, File.givenpath, Message.text,
                    Point, Range, Sut)
                    .outerjoin(Location)
                    .outerjoin(File)
                    .outerjoin(Point)
                    .outerjoin(Range, and_( # TOTEST
                        Range.start_id==Point.id, Range.end_id==Point.id))
                    .outerjoin(Analysis)
                    .outerjoin(Metadata)
                    .outerjoin(Sut)
                    .outerjoin(Message)
                    .filter(*clauses))
        
        if "q" in request_args.keys():
            # /search?q=sut.name:hello%20sut.version:blabla...
            clean_args = get_clean_args_from_query(request_args["q"])
        elif len(request_args) > 0:
            # /search?sut.name=hello&sut.version=blabla...
            clean_args = [(name, value) for name, value
                          in request_args.iteritems()]
        else: # no search
            return [], dict()

        filter_, clauses = get_filter_clauses_from_clean_args(clean_args)
        
        # TODO: polymorphism?
        q_issue = make_q(Issue, clauses)
        q_failure = make_q(Failure, clauses)
        q_info = make_q(Info, clauses)
        elem = q_issue.union(q_failure, q_info).all()
        
        return (to_dict(elem), filter_)

    def id(self, id, with_metadata=True):
        if not(with_metadata):
            return super(Result_app, self).id(id)
        else:
            elem = session.query(Result, Metadata).filter(and_(
                    Result.id == id,
                    Result.analysis_id == Analysis.id,
                    Analysis.metadata_id == Metadata.id)).first()
            return to_dict(elem)
