from lib.firehose_orm import Message, Analysis, Generator, Sut
# Message is already bound to a MetaData() object in firehose_orm

from app import session

class Message_app(object):
    def __init__(self):
        self.message = session.query(Message).first()
    
    def __repr__(self):
        return self.message.__repr__()

class Analysis_app(object):
    def __init__(self):
        self.analyses = session.query(Analysis).all()
    
    def all(self):
        return self.analyses

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
