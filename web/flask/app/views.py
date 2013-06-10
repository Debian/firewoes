from flask import render_template, jsonify
from flask.views import View

from app import app
from models import Generator_app, Analysis_app
from models import Http404Error, Http500Error



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
    def __init__(self, render_func=jsonify, err_func=lambda *x: x, **kwargs):
        self.render_func = render_func
        self.err_func = err_func
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])
    
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
    def get_objects(self):
        return dict()
        # meta_info = MetaInfo()
        # return dict(generators = meta_info.get_generators(),
        #             suts = meta_info.get_suts(),
        #             analyses = meta_info.get_analyses())

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


### FIREHOSE ELEMENT/LIST ###

class ElemView(GeneralView):
    def get_objects(self, id=None):
        obj = self.class_()
        result = obj.id(id)
        return dict(result=result)#dict(result=result)

class ListView(GeneralView):
    def get_objects(self):
        obj = self.class_()
        result = obj.all()
        return dict(list=result)#dict(result=result)

# GENERATOR # HTML
app.add_url_rule('/view/generator/<int:id>/', view_func=ElemView.as_view(
        'generator_elem_html',
        class_=Generator_app,
        render_func=lambda **kwargs: render_template('generator.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

app.add_url_rule('/view/generator/', view_func=ListView.as_view(
        'generator_list_html',
        class_=Generator_app,
        render_func=lambda **kwargs: render_template('generator_list.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

# GENERATOR # JSON
app.add_url_rule('/api/view/generator/<int:id>/', view_func=ElemView.as_view(
        'generator_elem_json',
        class_=Generator_app,
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))

app.add_url_rule('/api/view/generator/', view_func=ListView.as_view(
        'generator_list_json',
        class_=Generator_app,
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))


# ANALYSIS # HTML
app.add_url_rule('/view/analysis/<int:id>/', view_func=ElemView.as_view(
        'analysis_elem_html',
        class_=Analysis_app,
        render_func=lambda **kwargs: render_template('analysis.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

app.add_url_rule('/view/analysis/', view_func=ListView.as_view(
        'analysis_list_html',
        class_=Analysis_app,
        render_func=lambda **kwargs: render_template('analysis_list.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

# ANALYSIS # JSON
app.add_url_rule('/api/view/analysis/<int:id>/', view_func=ElemView.as_view(
        'analysis_elem_json',
        class_=Analysis_app,
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))

app.add_url_rule('/api/view/analysis/', view_func=ListView.as_view(
        'analysis_list_json',
        class_=Analysis_app,
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))
