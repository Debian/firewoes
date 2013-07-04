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

import os

from flask import render_template, jsonify, request, Blueprint, url_for
from flask.views import View

from firewose.web.app import app
from models import Generator_app, Analysis_app, Sut_app, Result_app
from models import Report
from models import Http404Error, Http500Error
from sources_link import get_source_url
#from forms import SearchForm

# Theme configuration
theme = app.config["THEME"]
static_folder = os.path.join("themes", theme, "static")
template_folder = os.path.join("themes", theme, "templates")

# Blueprint creation
mod = Blueprint('frontend', __name__,
                static_folder=static_folder,
                template_folder=template_folder,
                static_url_path="/frontend/static")
# we have to provide static_url_path to avoid a bug in Flask
# When a blueprint is registered without an url_prefix, its static folder
# remains the one from the app, unless we choose another name (eg /foo/static)
# see https://github.com/mitsuhiko/flask/issues/348

# JINJA2 CUSTOM FILTERS
@app.context_processor
def url_for_source():
    def url_for_source(package, version, release, path,
                       start_line, end_line=None,
                       message=None, embedded=False):
        if embedded:
            url_pattern = app.config["EMBEDDED_SOURCE_CODE_URL"]
        else:
            url_pattern = app.config["SOURCE_CODE_URL"]
        return get_source_url(url_pattern,
                              package, version, release, path,
                              start_line, end_line, message)
    return dict(url_for_source=url_for_source)

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

@mod.route('/')
def index():
    return render_template("index.html") # TODO: html()

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

add_firehose_view('analysis', Analysis_app)
add_firehose_view('result', Result_app)

### SEARCH ###

class SearchView(GeneralView):
    def get_objects(self):
        return Result_app().filter(request.args)

def render_html_search(templatename, **kwargs):
    """ adds pagination object before rendering """
    pagination = Pagination(kwargs['page'], kwargs['offset'],
                                    kwargs['results_all_count'])
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

### REPORT ###

class SearchReportView(GeneralView):
    def get_objects(self):
        try:
            name = request.args["package"]
        except:
            raise Http404Error
        return dict(packagename=name,
                    versions=Sut_app().versions(name))

# SEARCH REPORT (HTML)
mod.add_url_rule('/report/', view_func=SearchReportView.as_view(
        'search_report_html',
        render_func=lambda **kwargs: html('report_search.html',
                                                        **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

# SEARCH REPORT (JSON)
mod.add_url_rule('/api/report/', view_func=SearchReportView.as_view(
        'search_report_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))

class ReportView(GeneralView):
    def get_objects(self, package_id):
        return Report(package_id).all()

# REPORT (HTML)
mod.add_url_rule('/report/<package_id>', view_func=ReportView.as_view(
        'report_html',
        render_func=lambda **kwargs: html('report.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

# REPORT (JSON)
mod.add_url_rule('/api/report/<package_id>', view_func=ReportView.as_view(
        'report_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))
