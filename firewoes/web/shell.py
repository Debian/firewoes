import os
import readline
from pprint import pprint
import rlcompleter
readline.parse_and_bind("tab: complete")


from firewoes.web.app import *
from app.frontend.models import *
from firehose.model import *
from firewoes.lib.debianutils import *

os.environ['PYTHONINSPECT'] = 'True'
