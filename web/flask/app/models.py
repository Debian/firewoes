from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, Generator, Sut
#from lib.firehose_noslo

from app import session


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
    elif type(elem) in [int, float, str, unicode]:#_string_type]
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

class Analysis_app(FHGeneric):
    def __init__(self):
        self.fh_class = Analysis

    def all(self):
        elem = session.query(Analysis.id).all()
        return to_dict(elem)

    def id(self, id):
        elem = session.query(Analysis).filter(Analysis.id == id).first()
        elem = to_dict(elem)
        elem['results'] = to_dict(session.query(Result.id).filter(Result.analysis_id == id).all())
        return elem

class Sut_app(FHGeneric):
    def __init__(self):
        self.fh_class = Sut
