from flask import render_template

from app import app
from models import Message_app, Analysis_app, MetaInfo


### GENERAL VIEW HANDLING ###

class GeneralView(View):
    def __init__(self, render_func=jsonify, err_func=lambda *x: x):
        self.render_func = render_func
        self.err_func = err_func
    
    def dispatch_request(self, **kwargs):
        try:
            context = self.get_objects(**kwargs)
            return self.render_func(**context)
        except Http500Error as e:
            return self.err_func(e, http=500)
        except Http404Error as e:
            return self.err_func(e, http=404)


### INDEX ###

@app.route('/')
def index():
    meta_info = MetaInfo()
    return render_template("index.html",
                           generators = meta_info.get_generators(),
                           suts = meta_info.get_suts())


