from flask import render_template, jsonify, request, Blueprint
from flask.views import View

from app import app
from models import Generator_app, Analysis_app, Sut_app, Result_app
from models import Http404Error, Http500Error
#from forms import SearchForm

mod = Blueprint('firewose', __name__, template_folder='templates')

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
        return html('404.html'), 404

def deal_500_error(error, mode='html'):
    """ logs a 500 error and returns the correct template """
    # app.logger.error(error)
    
    if mode == 'json':
        return jsonify(dict(error=500))
    else:
        return html('500.html'), 500

### HTML FUNCTION ###

def html(templatename, **kwargs):
    return render_template(templatename, **kwargs)


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
        return dict(generators = Generator_app().all())

mod.add_url_rule('/', view_func=IndexView.as_view(
        'index_html',
        render_func=lambda **kwargs: html('index.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

mod.add_url_rule('/api/', view_func=IndexView.as_view(
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

def add_firehose_view(name, class_):
    def add_(name, class_, api=""):
        if api == "":
            mode = 'html'
        else:
            mode = 'json'
            api = '/'+api
        
        # LIST VIEW
        if mode == "html":
            render_func = lambda **kwargs:html('%s_list.html' %name, **kwargs)
        else:
            render_func = jsonify
        mod.add_url_rule('%s/view/%s/' % (api, name),
                         view_func=ListView.as_view(
                '%s_list_%s' % (name, mode),
                class_=class_,
                render_func=render_func,
                err_func=lambda e, **kwargs: deal_error(e, mode=mode, **kwargs)
                ))
        # ELEM VIEW
        if mode == "html":
            render_func = lambda **kwargs:html('%s.html' %name, **kwargs)
        else:
            render_func = jsonify
        mod.add_url_rule('%s/view/%s/<int:id>/' % (api, name),
                         view_func=ElemView.as_view(
                '%s_elem_%s' % (name, mode),
                class_=class_,
                render_func=render_func,
                err_func=lambda e, **kwargs: deal_error(e, mode=mode, **kwargs)
                ))
        
    add_(name, class_) # HTML
    add_(name, class_, api="api") # JSON

add_firehose_view('generator', Generator_app)
add_firehose_view('analysis', Analysis_app)
add_firehose_view('sut', Sut_app)
add_firehose_view('result', Result_app)

### FILTERS ###

def get_filter_from_url_params(request_args):
    try: packagename = request_args['packagename']
    except: packagename = ""
    
    if packagename != "":
        try: packageversion = request_args['packageversion']
        except: packageversion = ""
    else:
        packageversion = ""
    
    try: generatorname = request_args['generatorname']
    except: generatorname = ""
    
    if generatorname != "":
        try: generatorversion = request_args['generatorversion']
        except: generatorversion = ""
    else:
        generatorversion = ""
    
    return dict(packagename=packagename,
                packageversion=packageversion,
                generatorname=generatorname,
                generatorversion=generatorversion)


# class FilterListView(GeneralView):
#     def get_objects(self):
#         filter_ = get_filter_from_url_params(request.args)
#         #results = Result_app().filter(**filter_)
#         results = []
        
#         from filters import Filter
#         f = Filter()
#         f.add_elem("software name", Sut.name, value=filter_['packagename'])

#         global searchform # uuuuuuuuuuuuuuugh
#         searchform = f.get_form()
        
        
#         return dict(list=results, filter=filter_)

# # FILTER LIST HTML
# mod.add_url_rule('/filter/', view_func=FilterListView.as_view(
#         'filterlist_html',
#         render_func=lambda **kwargs: html('filter_list.html', **kwargs),
#         err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
#         ))

# # FILTER LIST JSON
# mod.add_url_rule('/api/filter/', view_func=FilterListView.as_view(
#         'filterlist_json',
#         render_func=jsonify,
#         err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
#         ))
