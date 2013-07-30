import os
import readline
from pprint import pprint
import rlcompleter
readline.parse_and_bind("tab: complete")


from firewose.web.app import *
from app.frontend.models import *
from firewose.lib.firehose_noslots import *
from firewose.lib.debianutils import *

os.environ['PYTHONINSPECT'] = 'True'
