import os
import readline
from pprint import pprint
import rlcompleter
readline.parse_and_bind("tab: complete")


from app import *
from app.firewose.models import *
from lib.firehose_noslots import *

os.environ['PYTHONINSPECT'] = 'True'
