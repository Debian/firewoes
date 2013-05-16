import os
import readline
from pprint import pprint

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

#import sys
#parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#sys.path.insert(0,parentdir) 
#from modules.ormapping import metadata, Z1
from experiments_model import metadata, Z1

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://' # in-memory
app.config['SQLALCHEMY_ECHO'] = True


db = SQLAlchemy(app)

########################
# do experiments here! #
########################

#from firehose_noslots import *

## todo: Z1.query=db.session.query_property()


"""
class Z2(object):
    def __init__(self, c):
        self.c = c

t_z2 = db.Table('z2',
                db.Column('c', db.Integer, primary_key=True),
                db.Column('ref_a', db.Integer),
                db.Column('ref_b', db.Integer),
                db.ForeignKeyConstraint(['ref_a', 'ref_b'], ['z1.a', 'z1.b'])
                )
db.mapper(Z2, t_z2,
          properties={
            'ccc': db.relationship(Z1, backref='z2'),
            }
          )
"""


metadata.create_all(bind=db.engine)


os.environ['PYTHONINSPECT'] = 'True'
