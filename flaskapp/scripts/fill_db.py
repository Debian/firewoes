import os
import glob
import firehose_noslots as fhm
from pprint import pprint


from flask import *
from app import *

db.drop_all()
db.create_all()

an = [fhm.Analysis.from_xml(file) for file in glob.glob("../debcocci/misc-code/generate_fake_base/*.xml")]

for a in an:
    db.session.merge(a)
    db.session.commit()
#db.session.add_all(an)
#db.session.commit()

pprint(db.session.query(models.Generator).all())

os.environ['PYTHONINSPECT'] = 'True'
