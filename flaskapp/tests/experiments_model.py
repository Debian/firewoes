from sqlalchemy import Table, MetaData, Column, \
    ForeignKey, Integer, String, Float
from sqlalchemy.orm import mapper, relationship, polymorphic_union, \
    sessionmaker

metadata = MetaData()

#def get_map(db):
class Z1(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

t_z1 = Table('z1', metadata,
             Column('a', Integer, primary_key=True),
             Column('b', Integer, primary_key=True),
             )
mapper(Z1, t_z1)

# TODO: remove side-effects
def set_tables(metadata):
    pass


def get_session(engine):
    metadata = MetaData(engine)
    set_tables(metadata)
    Session = sessionmaker(bind=engine)
    session = Session(bind=engine)
    
    return session

