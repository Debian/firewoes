import os, sys

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

app.config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '../../../etc/webconfig.py'))

sys.path.insert(0, app.config['ROOT_FOLDER'])

# SQLAlchemy
engine = create_engine(app.config['DATABASE_URI'],
                       echo=app.config['DEBUG'])
Session = sessionmaker(bind=engine, autoflush=True)
session = Session()


#import views

from app.firewose.views import mod as uiModule
app.register_blueprint(uiModule)
