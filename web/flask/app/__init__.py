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


import os, sys

from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class CustomFlask(Flask):
    # we deal with jinja2 options to remove whitespace
    jinja_options = dict(
        Flask.jinja_options, trim_blocks=True, lstrip_blocks=True)

app = CustomFlask(__name__)

# loads global and local configurations
app.config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '../../../etc/webconfig.py'))
app.config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '../../../etc/webconfig_local.py'))

sys.path.insert(0, app.config['ROOT_FOLDER'])

# SQLAlchemy
engine = create_engine(app.config['DATABASE_URI'],
                       echo=app.config['SQLALCHEMY_ECHO'])
Session = sessionmaker(bind=engine, autoflush=True)
session = Session()


from app.firewose.views import mod as firewose_module
app.register_blueprint(firewose_module)

# 404 / 500 errors

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500
