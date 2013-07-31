# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewoes.
#
# Firewoes is free software: you can redistribute it and/or modify it under
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


import os, sys

from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import logging
from logging import Formatter, StreamHandler

class CustomFlask(Flask):
    # we deal with jinja2 options to remove whitespace
    jinja_options = dict(
        Flask.jinja_options, trim_blocks=True, lstrip_blocks=True)

app = CustomFlask(__name__)

# Configuration
from firewoes.web import webconfig_default
app.config.from_object(webconfig_default)

if "FIREWOES_CONFIG" in os.environ:
    app.config.from_envvar('FIREWOES_CONFIG')

# SQLAlchemy
engine = create_engine(app.config['DATABASE_URI'],
                       echo=app.config['SQLALCHEMY_ECHO'])
session = scoped_session(sessionmaker(bind=engine, autoflush=True))
#session = Session()

from frontend.views import mod as frontend_module
app.register_blueprint(frontend_module)

# 404 / 500 errors

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    app.logger.error(e)
    return render_template('500.html'), 500

@app.teardown_appcontext
def shutdown_session(exception=None):
    session.remove()


# logging
handler = StreamHandler()
handler.setFormatter(Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'
        ))
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
