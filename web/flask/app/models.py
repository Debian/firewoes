from lib.firehose_orm import Analysis, Result, Generator, Sut

from app import session


### EXCEPTIONS ###

class Http500Error(Exception): pass
class Http404Error(Exception): pass


### MODEL CLASSES ###

class MetaInfo(object):
    def __init__(self):
        self.generators = session.query(Generator).all()
        self.suts = session.query(Sut).all()

    def get_generators(self):
        r = []#dict()
        for gen in self.generators:
            r.append(dict(name=gen.name, version=gen.version))
        return r
        #return self.get_generators

    def get_suts(self):
        r = []
        for s in self.suts:
            r.append(dict(name=s.name, version=s.version, type=s.type))
        return r


class Analysis_app(object):
    def __init__(self):
        self.analyses = session.query(Analysis).all()
    
    def all(self):
        return self.analyses


class Result_app(object):
    def __init__(self, id):
        self.result = session.query(Result).filter(Result.id == id).first()
        if not(self.result):
            raise Http404Error("Result with id %d doesn't exist." % id)
        
    def infos(self):
        return self.result


# class Message_app(object):
#     def __init__(self):
#         self.message = session.query(Message).first()
    
#     def __repr__(self):
#         return self.message.__repr__()
