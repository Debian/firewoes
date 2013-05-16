# Application model, derivated from Firehose
# ORM between database and Firehose classes


from app import db

#import firehose.model as fhm
from firehose_noslots import *

class Tbase(object):
    """
    As long as the declarative approach of SQLAlchemy cannot be used
    (because we map Firehose classes rather than here-made classes),
    this class provides the query interface from SQLAlchmy.
    """
    query = db.session.query_property()

# We subclass all Firehose classes
# Firehose uses __slots__ for memory optimisation, therefore we can't
# dynamically add attributes to a Firehose object. SQLAlchemy needs
# this, and here it becomes possible for subclasses.
# TODO: de-ugly-ize this situation
"""class Analysis(fhm.Analysis, Tbase): pass
class Result(fhm.Result, Tbase): pass
class Issue(fhm.Issue, Result, Tbase): pass
class Failure(fhm.Failure, Result, Tbase): pass
class Info(fhm.Info, Result, Tbase): pass
class Metadata(fhm.Metadata, Tbase): pass
class Generator(fhm.Generator, Tbase): pass
class Sut(fhm.Sut, Tbase): pass
class SourceRpm(fhm.SourceRpm, Sut, Tbase): pass
class DebianBinary(fhm.DebianBinary, Sut, Tbase): pass
class DebianSource(fhm.DebianSource, Sut, Tbase): pass
class Stats(fhm.Stats, Tbase): pass
class Message(fhm.Message, Tbase): pass
class Notes(fhm.Notes, Tbase): pass
class Trace(fhm.Trace, Tbase): pass
class State(fhm.State, Tbase): pass
class Location(fhm.Location, Tbase): pass
class File(fhm.File, Tbase): pass
class Hash(fhm.Hash, Tbase): pass
class Function(fhm.Function, Tbase): pass
class Point(fhm.Point, Tbase): pass
class Range(fhm.Range, Tbase): pass
class CustomFields(fhm.CustomFields, Tbase): pass
"""

class Message2(Message):
    #def __init__(self, text):
    #    super(Message2, self).__init__(text)
    pass

# imported from firehose-orm/orm.py:

############################################################################
# Tables
############################################################################

t_analysis = \
    db.Table('analysis',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('metadata_id', db.Integer,
                       db.ForeignKey('metadata.id'), nullable=False),
             db.Column('customfields_id', db.Integer,
                       db.ForeignKey('customfields.id')),
             )

t_metadata = \
    db.Table('metadata',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('generator_id', db.Integer,
                       db.ForeignKey('generator.id'), nullable=False),
             db.Column('sut_id', db.Integer, db.ForeignKey('sut.id')),
             db.Column('file_id', db.Integer, db.ForeignKey('file.id')),
             db.Column('stats_id', db.Integer, db.ForeignKey('stats.id')),
             )

t_stats = \
    db.Table('stats',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('wallclocktime', db.Float, nullable=False),
             )

t_generator = \
    db.Table('generator',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('name',  db.String, nullable=False),
             db.Column('version',  db.String),
             )

# For the Sut hierarchy we use single-table inheritance
t_sut = \
    db.Table('sut',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('type', db.String(20), nullable=False),
             db.Column('name',  db.String, nullable=False),
             db.Column('version',  db.String, nullable=False),
             db.Column('release',  db.String),
             db.Column('buildarch',  db.String),
             )

# For the Result hierarchy we use joined-table inheritance
t_result = \
    db.Table('result',
             db.Column('id', db.Integer, primary_key=True), # renamed from result_id
             db.Column('analysis_id', db.Integer,
                       db.ForeignKey('analysis.id'), nullable=False),
             db.Column('type', db.String(10), nullable=False),
             )

t_issue = \
    db.Table('issue',
             db.Column('result_id', db.Integer,
                       db.ForeignKey('result.id'), primary_key=True),
             db.Column('cwe', db.Integer),
             db.Column('testid', db.String),
             db.Column('location_id', db.Integer,
                       db.ForeignKey('location.id'), nullable=False),
             db.Column('message_id',  db.Integer,
                       db.ForeignKey('message.id'), nullable=False),
             db.Column('notes_id',  db.Integer, db.ForeignKey('notes.id')),
             db.Column('trace_id',  db.Integer, db.ForeignKey('trace.id')),
             db.Column('severity',  db.String),
             db.Column('customfields_id', db.Integer,
                       db.ForeignKey('customfields.id')),
             )

t_failure = \
    db.Table('failure',
             db.Column('result_id', db.Integer,
                       db.ForeignKey('result.id'),
                       primary_key=True),
             db.Column('failureid', db.String),
             db.Column('location_id', db.Integer,
                       db.ForeignKey('location.id')),
             db.Column('message_id',  db.Integer,
                       db.ForeignKey('message.id')),
             db.Column('customfields_id', db.Integer,
                       db.ForeignKey('customfields.id')),
             )

t_info = \
    db.Table('info',
             db.Column('result_id', db.Integer,
                       db.ForeignKey('result.id'), primary_key=True),
             db.Column('infoid', db.String),
             db.Column('location_id', db.Integer,
                       db.ForeignKey('location.id')),
             db.Column('message_id',  db.Integer,
                       db.ForeignKey('message.id')),
             db.Column('customfields_id', db.Integer,
                       db.ForeignKey('customfields.id')),
          )

t_message = \
    db.Table('message',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('text', db.String, nullable=False),
             )
# ideally we should just store a String where these get used

t_notes = \
    db.Table('notes',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('text', db.String, nullable=False),
             )
# ideally we should just store a String where these get used


t_trace = \
    db.Table('trace',
             db.Column('id', db.Integer, primary_key=True)
             )

t_state = \
    db.Table('state',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('trace_id',  db.Integer,
                       db.ForeignKey('trace.id')),
             db.Column('location_id', db.Integer,
                       db.ForeignKey('location.id'), nullable=False),
             db.Column('notes_id',  db.Integer,
                       db.ForeignKey('notes.id')),
             )

t_location = \
    db.Table('location',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('file_id', db.Integer,
                       db.ForeignKey('file.id'), nullable=False),
             db.Column('function_id', db.Integer,
                       db.ForeignKey('function.id')),
             db.Column('point_id', db.Integer,
                       db.ForeignKey('point.id')),
             db.Column('range_id', db.Integer,
                       db.ForeignKey('range.id')),
             )

t_file = \
    db.Table('file',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('givenpath', db.String, nullable=False),
             db.Column('abspath', db.String),
             db.Column('hash_id', db.Integer, db.ForeignKey('hash.id')),
             )

t_hash = \
    db.Table('hash',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('alg', db.String, nullable=False),
             db.Column('hexdigest', db.String, nullable=False),
             )

t_function = \
    db.Table('function',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('name', db.String, nullable=False),
                  # in firehose: can be None
             )

t_point = \
    db.Table('point',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('line', db.Integer, nullable=False),
             db.Column('column', db.Integer, nullable=False),
             )

t_range = \
    db.Table('range',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('start_id', db.Integer,
                       db.ForeignKey('point.id'), nullable=False),
             db.Column('end_id', db.Integer,
                       db.ForeignKey('point.id'), nullable=False),
             )

t_customfields = \
    db.Table('customfields',
             db.Column('id', db.Integer, primary_key=True))

t_intfield = \
    db.Table('intfield',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('customfields_id', db.Integer,
                       db.ForeignKey('customfields.id'), nullable=False),
             db.Column('name', db.String, nullable=False),
             db.Column('value', db.Integer, nullable=False),
             )

t_strfield = \
    db.Table('strfield',
             db.Column('id', db.Integer, primary_key=True),
             db.Column('customfields_id', db.Integer,
                       db.ForeignKey('customfields.id'), nullable=False),
             db.Column('name', db.String, nullable=False),
             db.Column('value', db.String, nullable=False),
             )

############################################################################
# Mappers
############################################################################

db.mapper(Analysis, t_analysis,
          properties={
            'metadata' : db.relationship(Metadata),
            # FIXME: should do both issues *and* failures
            'results' : db.relationship(Result), #, backref='analysis', order_by=t_issue.c.id)
            'customfields' : db.relationship(CustomFields),
            }
          )

db.mapper(Metadata, t_metadata,
          properties={
            'generator' : db.relationship(Generator),
            'sut' : db.relationship(Sut),
            'file_' : db.relationship(File),
            'stats' : db.relationship(Stats),
            }
          )

db.mapper(Generator, t_generator)

# Map the Sut hierarchy using single table inheritance
sut_mapper = db.mapper(Sut, t_sut,
                       polymorphic_on=t_sut.c.type,
                       polymorphic_identity='sut')

source_rpm_mapper = db.mapper(SourceRpm,
                             inherits=sut_mapper,
                             polymorphic_identity='source-rpm')

debian_binary_mapper = db.mapper(DebianBinary,
                             inherits=sut_mapper,
                             polymorphic_identity='debian-binary')

debian_source_mapper = db.mapper(DebianSource,
                             inherits=sut_mapper,
                             polymorphic_identity='debian-source')

db.mapper(Stats, t_stats)
db.mapper(Message, t_message)
db.mapper(Notes, t_notes)

db.mapper(Trace, t_trace,
          properties={
            'states' : db.relationship(State,
                                       backref='trace',
                                       order_by=t_state.c.id,
                                       lazy='joined')
            }
          )

db.mapper(State, t_state,
          properties={
            'location': db.relationship(Location, lazy='joined'),
            'notes': db.relationship(Notes, lazy='joined'),
            }
          )

# Map the Result hierarchy using Joined Table Inheritance:

db.mapper(Result, t_result,
          polymorphic_on=t_result.c.type,
          polymorphic_identity='result')

db.mapper(Issue, t_issue,
          inherits=Result,
          polymorphic_identity='issue',
          properties={
            'location' : db.relationship(Location,
                                         backref='issues',
                                         order_by=t_location.c.id,
                                         lazy='joined'),
            'message':  db.relationship(Message, lazy='joined'),
            'notes':  db.relationship(Notes, lazy='joined'),
            'trace' : db.relationship(Trace, lazy='joined'),
            'customfields' : db.relationship(CustomFields),
            }
          )

db.mapper(Failure, t_failure,
          inherits=Result,
          polymorphic_identity='failure',
          properties={
            'location' : db.relationship(Location),
            'message' : db.relationship(Message),
            'customfields' : db.relationship(CustomFields),
            }
          )

db.mapper(Info, t_info,
          inherits=Result,
          polymorphic_identity='info',
          properties={
            'location' : db.relationship(Location),
            'message' : db.relationship(Message),
            'customfields' : db.relationship(CustomFields),
            }
          )

db.mapper(Location, t_location,
          properties={
            'file' : db.relationship(File, lazy='joined'),
                    #, backref='locations', order_by=t_file.c.abspath)
            'function' : db.relationship(Function, lazy='joined'),
            'point' : db.relationship(Point, lazy='joined'),
            'range_' : db.relationship(Range, lazy='joined'),
            }
          )

db.mapper(File, t_file,
          properties={
            'hash_' : db.relationship(Hash, lazy='joined'),
            }
          )

db.mapper(Hash, t_hash)
db.mapper(Function, t_function)
db.mapper(Point, t_point)
db.mapper(Range, t_range)
db.mapper(CustomFields, t_customfields)

