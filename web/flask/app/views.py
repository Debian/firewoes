from flask import render_template, jsonify
from flask.views import View

from app import app
from models import Message_app, Analysis_app, MetaInfo


### EXCEPTIONS ###

class Http500Error(Exception): pass
class Http404Error(Exception): pass


### ERRORS ###

def deal_error(error, http=404, mode='html'):
    if http == 404:
        return deal_404_error(error, mode)
    elif http == 500:
        return deal_500_error(error, mode)
    else:
        raise Exception("Unimplemented HTTP error: %s" % str(http))

def deal_404_error(error, mode='html'):
    if mode == 'json':
        return jsonify(dict(error=404))
    else:
        return render_template('404.html'), 404

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

def deal_500_error(error, mode='html'):
    """ logs a 500 error and returns the correct template """
    # app.logger.error(error)
    
    if mode == 'json':
        return jsonify(dict(error=500))
    else:
        return render_template('500.html'), 500

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


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

class IndexView(GeneralView):
    def get_objects(self, query=None):
        meta_info = MetaInfo()
        return dict(generators = meta_info.get_generators(),
                    suts = meta_info.get_suts())

app.add_url_rule('/', view_func=IndexView.as_view(
        'index_html',
        render_func=lambda **kwargs: render_template('index.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

app.add_url_rule('/api/', view_func=IndexView.as_view(
        'index_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))

