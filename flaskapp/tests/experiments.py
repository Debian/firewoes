import os
import readline
from pprint import pprint

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

#import sys
#parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#sys.path.insert(0,parentdir) 

#from experiments_model import metadata, Z1

app = Flask(__name__)

app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://' # in-memory
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app, session_options=dict(autocommit=False, autoflush=True))

########################
# do experiments here! #
########################

#from firehose_noslots import *

## todo: Z1.query=db.session.query_property()

class An(object):
    def __init__(self, an_name, gen):
        self.an_name = an_name
        self.gen = gen

class Gen(object):
    def __init__(self, gen_name):
        self.gen_name =gen_name

t_an = db.Table('an',
                db.Column('id', db.Integer, primary_key=True),
                db.Column('an_name', db.String),
                db.Column('gen_id', db.Integer, db.ForeignKey('gen.gen_name')),
                )
db.mapper(An, t_an,
          properties={
            'gen': db.relationship(Gen),
            }
          )
t_gen = db.Table('gen',
                 #db.Column('id', db.Integer, primary_key=True),
                 db.Column('gen_name', db.String, primary_key=True),
                 )
db.mapper(Gen, t_gen)

db.drop_all()
db.create_all()

gen1 = Gen("coccinelle")
gen2 = Gen("coccinelle")

an1 = An("an1", gen1)
an2 = An("an2", gen2)

db.session.merge(an1)
#db.session.commit()
db.session.merge(an2)
db.session.commit()

os.environ['PYTHONINSPECT'] = 'True'
