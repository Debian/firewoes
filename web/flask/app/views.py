from flask import render_template, jsonify, request
from flask.views import View

from app import app
from models import Generator_app, Analysis_app, Sut_app, Result_app
from models import Http404Error, Http500Error
from forms import SearchForm



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

@app.errorhandler(404)
def page_not_found(e):
    return html('404.html'), 404

def deal_500_error(error, mode='html'):
    """ logs a 500 error and returns the correct template """
    # app.logger.error(error)
    
    if mode == 'json':
        return jsonify(dict(error=500))
    else:
        return html('500.html'), 500

@app.errorhandler(500)
def server_error(e):
    return html('500.html'), 500

### HTML FUNCTION ###

def html(templatename, **kwargs):
    # search form preprocessing
    searchform = SearchForm()
    try:
        filter_ = kwargs['filter']
    except:
        filter_ = None
    if filter_ is not None:
        if filter_['packagename'] != "":
            versions = Sut_app().versions(filter_['packagename'])
            searchform.packageversion.choices = [('', '(all)')]
            searchform.packageversion.choices += [
                (vers['version'], vers['version']) for vers in versions]
            # default selected choice:
            searchform.packageversion.data = filter_['packageversion']
    
    generators = Generator_app().unique_by_name()
    
    searchform.generatorname.choices = [('', '(all)')]
    searchform.generatorname.choices += [
        (gen['name'], gen['name']) for gen in generators]
    if filter_ is not None:
        if filter_['generatorname'] != "": # we add the versions
            searchform.generatorversion.choices = [('', '(all)')]
            versions = Generator_app().versions(filter_['generatorname'])
            searchform.generatorversion.choices += [
                (vers['version'], vers['version']) for vers in versions]
            
            
            # default selected choice:
            searchform.generatorname.data = filter_['generatorname']
            searchform.generatorversion.data = filter_['generatorversion']
    
    return render_template(templatename,
                           searchform=searchform,
                           **kwargs)


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

app.add_url_rule('/', view_func=IndexView.as_view(
        'index_html',
        render_func=lambda **kwargs: html('index.html', **kwargs),
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
        app.add_url_rule('%s/view/%s/' % (api, name),
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
        app.add_url_rule('%s/view/%s/<int:id>/' % (api, name),
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

# class FilterView(GeneralView):
#     def get_objects(self):
#         # we get the list of result.id linked to the specified package
#         filter_ = get_filter_from_url_params(request.args)
#         list_ = Result_app().filter(**filter_)        
        
#         # we get the current viewed result
#         if len(list_) == 0:
#             current_result = None
#             previous_result = None
#             next_result = None
#             current_result_range = None
#         else:
#             try:
#                 current_result_id = int(get['id'])
#             except: # default
#                 current_result_id = list_[0]['id']

#             current_result = Result_app().id(current_result_id,
#                                              with_metadata=True)
            
#             # we get the previous and next results (for links)
#             for i, elem in enumerate(list_):
#                 if elem['id'] == current_result_id:
#                     break
#             current_result_range = i
#             if current_result_range == 0:
#                 previous_result = None
#             else:
#                 previous_result = list_[current_result_range-1]['id']
#             if current_result_range == len(list_) - 1:
#                 next_result = None
#             else:
#                 next_result = list_[current_result_range+1]['id']
#             current_result_range += 1 # humans don't start at 0
        
#         return dict(list=list_,
#                     filter=filter_,
#                     current_result=current_result,
#                     current_result_range=current_result_range,
#                     previous_result=previous_result, next_result=next_result)

class FilterListView(GeneralView):
    def get_objects(self):
        filter_ = get_filter_from_url_params(request.args)
        results = Result_app().filter(**filter_)
        
        return dict(list=results, filter=filter_)

# FILTER LIST HTML
app.add_url_rule('/filter/', view_func=FilterListView.as_view(
        'filterlist_html',
        render_func=lambda **kwargs: html('filter_list.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

# FILTER LIST JSON
app.add_url_rule('/api/filter/', view_func=FilterListView.as_view(
        'filterlist_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))


# # FILTER HTML
# app.add_url_rule('/filter/', view_func=FilterView.as_view(
#         'filter_html',
#         render_func=lambda **kwargs: html('filter.html', **kwargs),
#         err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
#         ))

# # FILTER JSON
# app.add_url_rule('/api/filter/', view_func=FilterView.as_view(
#         'filter_json',
#         render_func=jsonify,
#         err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
#         ))
