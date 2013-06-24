# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewose.
#
# Firewose is free software: you can redistribute it and/or modify it under
# the terms of the GNU Affero General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
# details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


from flask import render_template, jsonify, request, Blueprint, url_for
from flask.views import View

from app import app
from models import Generator_app, Analysis_app, Sut_app, Result_app
from models import Http404Error, Http500Error
#from forms import SearchForm


mod = Blueprint('firewose', __name__, template_folder='templates')


### PAGINATION ###
from pagination import Pagination

def url_for_other_page(page):
    args = request.args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)
app.jinja_env.globals['url_for_other_page'] = url_for_other_page



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
    generators_by_name = Generator_app().unique_by_name()
    return render_template(templatename,
                           generators_by_name=generators_by_name,
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
        return dict()

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

### SEARCH ###

class SearchView(GeneralView):
    def get_objects(self):
        # results, filter_, precise_menu = Result_app().filter(request.args)
        # return dict(results=results,
        #             filter=filter_,
        #             precise_menu=precise_menu)
        return Result_app().filter(request.args)

def render_html_search(templatename, **kwargs):
    """ adds pagination object before rendering """
    #kwargs['pagination']
    pagination = Pagination(kwargs['page'], kwargs['offset'],
                                    kwargs['results_all_count'])
    #print(kwargs['pagination'])
    return html(templatename, pagination=pagination, **kwargs)

mod.add_url_rule('/search/', view_func=SearchView.as_view(
        'search_html',
        render_func=lambda **kwargs: render_html_search('search.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

mod.add_url_rule('/api/search/', view_func=SearchView.as_view(
        'search_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))
