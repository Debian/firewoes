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

from flask import render_template, jsonify, request, Blueprint, url_for, \
    redirect
from flask.views import View

from firewose.web.app import app
from models import Generator_app, Analysis_app, Sut_app, Result_app
from models import Report
from models import Http404Error, Http500Error

import fedorautils
import debianutils
from debianutils import get_source_url

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
            url_pattern = app.config["DEBIAN_EMBEDDED_SOURCES_URL"]
        else:
            url_pattern = app.config["DEBIAN_SOURCES_URL"]
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
    app.logger.exception(error)
    
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
    return html("index.html")

### RESULT DETAILS ###

class ResultView(GeneralView):
    def get_objects(self, id=None):
        result = Result_app().id(id)
        return dict(result=result)

mod.add_url_rule('/result/<id>/', view_func=ResultView.as_view(
        'result_elem_html',
        render_func=lambda **kwargs: html('result.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

mod.add_url_rule('/api/result/<id>/', view_func=ResultView.as_view(
        'result_elem_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))

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

# redirects the searches
@mod.route("/report/")
def search_report_html():
    try:
        name = request.args["package"]
    except:
        raise Http404Error
    return redirect(url_for('.report_html', package_name=name))

# returns the reports for each version of package_name
class ReportView(GeneralView):
    def get_objects(self, package_name):
        results = []
        for package in Sut_app().versions(package_name):
            results.append(
                dict(
                    package=package,
                    report=Report(package["id"]).all()))
        # we assume here all the versions for one package have the same type
        # (debiansrc/binary or fedora), because we can't order a mix
        if len(results) >= 1:
            if results[0]["package"]["type"] == "source-rpm":
                version_compare = fedorautils.version_compare
            else:
                version_compare = debianutils.version_compare
        
            results = sorted(results, cmp=version_compare,
                             key=lambda x: x["package"]["version"] +
                                           "-" + x["package"]["release"])
                                            # TODO: fedora?
        
        return dict(results=results,
                    package_name=package_name)
            
    
# REPORT (HTML)
mod.add_url_rule('/report/<package_name>/', view_func=ReportView.as_view(
        'report_html',
        render_func=lambda **kwargs: html('report.html', **kwargs),
        err_func=lambda e, **kwargs: deal_error(e, mode='html', **kwargs)
        ))

# REPORT (JSON)
mod.add_url_rule('/api/report/<package_name>/', view_func=ReportView.as_view(
        'report_json',
        render_func=jsonify,
        err_func=lambda e, **kwargs: deal_error(e, mode='json', **kwargs)
        ))
