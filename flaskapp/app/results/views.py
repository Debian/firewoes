from flask import Blueprint, render_template
from modules import ormapping

from app import db

mod = Blueprint('results', __name__, url_prefix='/results')

@mod.route('/show')

def show():
    generators = [(gen.name, gen.version)
                  for gen in db.session.query(ormapping.Generator).all()]
    results = db.session.query(ormapping.Result).all()
    
    return render_template('results/show.html',
                           title='show results',
                           generators=generators,
                           results=results)
