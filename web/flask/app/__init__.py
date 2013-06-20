import os, sys

from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class CustomFlask(Flask):
    # we deal with jinja2 options to remove whitespace
    jinja_options = dict(
        Flask.jinja_options, trim_blocks=True, lstrip_blocks=True)

app = CustomFlask(__name__)

app.config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '../../../etc/webconfig.py'))

sys.path.insert(0, app.config['ROOT_FOLDER'])

# SQLAlchemy
engine = create_engine(app.config['DATABASE_URI'],
                       echo=app.config['DEBUG'])
Session = sessionmaker(bind=engine, autoflush=True)
session = Session()


from app.firewose.views import mod as firewose_module
app.register_blueprint(firewose_module)

# 404 / 500 errors

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
