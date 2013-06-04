import os, sys

from flask import Flask

app = Flask(__name__)

app.config.from_pyfile(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '../../../etc/webconfig.py'))

sys.path.insert(0, app.config['ROOT_FOLDER'])

import views
