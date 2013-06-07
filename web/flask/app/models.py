from lib.firehose_orm import Analysis, Result, Generator, Sut

from app import session


### EXCEPTIONS ###

class Http500Error(Exception): pass
class Http404Error(Exception): pass


### MODEL CLASSES ###

class MetaInfo(object):
    def __init__(self):
        self.generators = Generator_app().all()
        self.suts = Sut_app().all()
        self.analyses = Analysis_app().last_ones()

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
    
    def get_analyses(self):
        r = []
        for a in self.analyses:
            r.append(dict(id = a.id, generator = a.metadata.generator.name))
                                                   # fixme
        return r


class Generator_app(object):
    def __init__(self):
        pass
    
    def all(self):
        return session.query(Generator).all()

class Sut_app(object):
    def __init__(self):
        pass
    
    def all(self):
        return session.query(Sut).all()

class Analysis_app(object):
    def __init__(self):
        pass
    
    def all(self):
        self.analyses = session.query(Analysis).all()
        return self.analyses
    
    def last_ones(self, n=10):
        self.last_ones = session.query(
            Analysis).order_by(Analysis.id.desc()).limit(n)
        return self.last_ones


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
