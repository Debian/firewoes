from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)

import os, sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 

from modules import ormapping

# metadata.create_all(bind=db.engine)
from app.results.views import mod as resultsModule
app.register_blueprint(resultsModule)

