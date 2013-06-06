from flask import render_template

from app import app
from models import Message_app, Analysis_app, MetaInfo

@app.route('/')
def index():
    meta_info = MetaInfo()
    return render_template("index.html",
                           generators = meta_info.get_generators(),
                           suts = meta_info.get_suts())

@app.route('/analyses/')
def analyses():
    analyses = Analysis_app()
    return render_template("analyses.html", analyses = analyses.all())
