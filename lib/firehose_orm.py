from sqlalchemy import Table, MetaData, Column, \
    ForeignKey, Integer, String, Float, ForeignKeyConstraint, \
    event, DDL
from sqlalchemy.orm import mapper, relationship, polymorphic_union, \
    sessionmaker
from sqlalchemy.schema import Sequence

metadata = MetaData()

from firehose_noslots import *


# imported from firehose-orm/orm.py:


# FH_UNICITY enables to create a tuple for each Firehose object
# it is used to ensure unique objects, database-side
# the tuple contains the name of the unique columns
# this is used by firehose_unique.get_fh_unique()

FH_UNICITY = dict(
    Generator = ("name", "version"),
    Metadata = ("sut", "file_", "stats"),
    Stats = ("wallcloktime"),
    #Sut = ("type", "name", "version", "release", "buildarch"),
    SourceRpm = ("name", "version", "release", "buildarch"),
    DebianBinary = ("name", "version", "release", "buildarch"),
    DebianSource = ("name", "version", "release"),
    #Result = ("analysis_id", "type"),
    #Issue = ("cwe", "testid", "severity", "message", "notes", "location",
    #         "trace", "customfields"),
    Message = ("text"),
    Notes = ("text"),
    Location = ("file", "function", "point", "range_"),
    File = ("givenpath", "abspath", "hash_"),
    Hash = ("alg", "hexdigest"),
    Function = ("name"),
    Point = ("line", "column"),
    Range = ("start", "end"),
    )



############################################################################
# Tables
############################################################################

t_analysis = \
    Table('analysis', metadata,
          Column('id', Integer, primary_key=True),
          Column('metadata_id', Integer,
                 ForeignKey('metadata.id'), nullable=False),
          Column('customfields_id', Integer,
                 ForeignKey('customfields.id')),
          )

t_generator = \
    Table('generator', metadata,
          Column('id', Integer, primary_key=True),
          Column('name', String),
          Column('version', String), # optional in RNG
          )

t_metadata = \
    Table('metadata', metadata,
          Column('id', Integer, primary_key=True),
          Column('generator_id', Integer,
                 ForeignKey('generator.id'), nullable=False),
          Column('sut_id', Integer, ForeignKey('sut.id')),
          Column('file_id', Integer, ForeignKey('file.id')),
          Column('stats_id', Integer, ForeignKey('stats.id')),
          )

t_stats = \
    Table('stats', metadata,
          Column('id', Integer, primary_key=True),
          Column('wallclocktime', Float, nullable=False),
          )

# For the Sut hierarchy we use joined-table inheritance
t_sut = \
    Table('sut', metadata,
          Column('id', Integer, primary_key=True),
          Column('type', String(20), nullable=False),
          Column('name', String, nullable=False),
          Column('version', String, nullable=False),
          Column('release', String),
          Column('buildarch', String),
          )

# t_sourcerpm = \
#     Table('sourcerpm', metadata,
#           Column('sut_id', Integer, ForeignKey('sut.id'), primary_key=True),
#           Column('name', String),
#           Column('version', String),
#           Column('release', String),
#           Column('buildarch', String),
#           )

# t_debianbinary = \
#     Table('debianbinary', metadata,
#           Column('sut_id', Integer, ForeignKey('sut.id'), primary_key=True),
#           Column('name', String),
#           Column('version', String),
#           Column('release', String),
#           Column('buildarch', String),
#           )

# t_debiansource = \
#     Table('debiansource', metadata,
#           Column('sut_id', Integer, ForeignKey('sut.id'), primary_key=True),
#           Column('name', String),
#           Column('version', String),
#           Column('release', String),
#           )


# For the Result hierarchy we use joined-table inheritance
t_result = \
    Table('result', metadata,
          Column('id', Integer, primary_key=True), # renamed from result_id
          Column('analysis_id', Integer,
                 ForeignKey('analysis.id'), nullable=False),
          Column('type', String(10), nullable=False),
          )

t_issue = \
    Table('issue', metadata,
          Column('result_id', Integer,
                 ForeignKey('result.id'), primary_key=True),
          Column('cwe', Integer),
          Column('testid', String),
          Column('severity', String),
          Column('message_id', Integer,
                 ForeignKey('message.id'), nullable=False),
          Column('notes_id', Integer, ForeignKey('notes.id')),
          Column('location_id', Integer,
                 ForeignKey('location.id'), nullable=False),
          Column('trace_id', Integer, ForeignKey('trace.id')),
          Column('customfields_id', Integer,
                 ForeignKey('customfields.id')),
          )

t_failure = \
    Table('failure', metadata,
          Column('result_id', Integer,
                 ForeignKey('result.id'), primary_key=True),
          Column('failureid', String),
          Column('location_id', Integer, ForeignKey('location.id')),
          Column('message_id', Integer, ForeignKey('message.id')),
          Column('customfields_id', Integer, ForeignKey('customfields.id')),
          )

t_info = \
    Table('info', metadata,
          Column('result_id', Integer,
                 ForeignKey('result.id'), primary_key=True),
          Column('infoid', String),
          Column('location_id', Integer, ForeignKey('location.id')),
          Column('message_id', Integer, ForeignKey('message.id')),
          Column('customfields_id', Integer, ForeignKey('customfields.id')),
          )

t_message = \
    Table('message', metadata,
          Column('id', Integer, primary_key=True),
          Column('text', String),
          )

t_notes = \
    Table('notes', metadata,
          Column('id', Integer, primary_key=True),
          Column('text', String),
          )

t_trace = \
    Table('trace', metadata,
          Column('id', Integer, primary_key=True)
          )

t_state = \
    Table('state', metadata,
          Column('id', Integer, primary_key=True),
          Column('trace_id', Integer, ForeignKey('trace.id')),
          Column('location_id', Integer,
                 ForeignKey('location.id'), nullable=False),
          Column('notes_id', Integer, ForeignKey('notes.id')),
          # annotation (key/value) pairs -> why not CustomFields here?
          )

t_location = \
    Table('location', metadata,
          Column('id', Integer, primary_key=True),
          Column('file_id', Integer, ForeignKey('file.id'), nullable=False),
          Column('function_id', Integer, ForeignKey('function.id')),
          # either a point or a range:
          Column('point_id', Integer, ForeignKey('point.id')),
          Column('range_id', Integer, ForeignKey('range.id')),
          )

t_file = \
    Table('file', metadata,
          Column('id', Integer, primary_key=True),
          Column('givenpath', String, nullable=False),
          Column('abspath', String),
          Column('hash_id', Integer, ForeignKey('hash.id')),
          )

t_hash = \
    Table('hash', metadata,
          Column('id', Integer, primary_key=True),
          Column('alg', String, nullable=False),
          Column('hexdigest', String, nullable=False),
          )

t_function = \
    Table('function', metadata,
          Column('id', Integer, primary_key=True),
          Column('name', String, nullable=False),
            # in firehose: can be None
          )

t_point = \
    Table('point', metadata,
          Column('id', Integer, primary_key=True),
          Column('line', Integer, nullable=False),
          Column('column', Integer, nullable=False),
          )

t_range = \
    Table('range', metadata,
          Column('id', Integer, primary_key=True),
          Column('start_id', Integer,
                 ForeignKey('point.id'), nullable=False),
          Column('end_id', Integer,
                 ForeignKey('point.id'), nullable=False),
          )

t_customfields = \
    Table('customfields', metadata,
          Column('id', Integer, primary_key=True))

# inheritance here?

t_intfield = \
    Table('intfield', metadata,
          Column('id', Integer, primary_key=True),
          Column('customfields_id', Integer,
                 ForeignKey('customfields.id'), nullable=False),
          Column('name', String, nullable=False),
          Column('value', Integer, nullable=False),
          )

t_strfield = \
    Table('strfield', metadata,
          Column('id', Integer, primary_key=True),
          Column('customfields_id', Integer,
                 ForeignKey('customfields.id'), nullable=False),
          Column('name', String, nullable=False),
          Column('value', String, nullable=False),
          )

############################################################################
# Mappers
############################################################################

mapper(Analysis, t_analysis,
       properties={
        'metadata': relationship(Metadata, lazy='joined'),
        # FIXME: should do both issues *and* failures
        'results': relationship(
            Result, order_by=t_result.c.id, lazy='noload'),
        'customfields': relationship(CustomFields),
        }
       )

mapper(Metadata, t_metadata,
       properties={
        'generator': relationship(Generator, lazy='joined'),
        'sut': relationship(Sut, lazy='joined'),
        'file_': relationship(File, lazy='joined'),
        'stats': relationship(Stats, lazy='joined'),
        }
       )

mapper(Generator, t_generator)

# Map the Sut hierarchy using single table inheritance
sut_mapper = mapper(Sut, t_sut,
                    polymorphic_on=t_sut.c.type,
                    polymorphic_identity='sut')

mapper(SourceRpm, #t_sourcerpm,
       inherits=sut_mapper,
       polymorphic_identity='source-rpm')

mapper(DebianBinary, #t_debianbinary,
       inherits=sut_mapper,
       polymorphic_identity='debian-binary')

mapper(DebianSource, #t_debiansource,
       inherits=sut_mapper,
       polymorphic_identity='debian-source')

mapper(Stats, t_stats)
mapper(Message, t_message)
mapper(Notes, t_notes)

mapper(Trace, t_trace,
       properties={
        'states': relationship(
            State, order_by=t_state.c.id, lazy='joined')
        }
       )

mapper(State, t_state,
       properties={
        'location': relationship(Location, lazy='joined'),
        'notes': relationship(Notes, lazy='joined'),
        }
       )

# Map the Result hierarchy using Joined Table Inheritance:

mapper(Result, t_result,
       polymorphic_on=t_result.c.type,
       polymorphic_identity='result',
       properties={
        'analysis': relationship(Analysis),
        }
       )

mapper(Issue, t_issue,
       inherits=Result,
       polymorphic_identity='issue',
       properties={
        'location': relationship(Location, lazy='joined'),
        'message':  relationship(Message, lazy='joined'),
        'notes':  relationship(Notes, lazy='joined'),
        'trace': relationship(Trace, lazy='joined'),
        'customfields': relationship(CustomFields),
        }
       )

mapper(Failure, t_failure,
       inherits=Result,
       polymorphic_identity='failure',
       properties={
        'location': relationship(Location, lazy='joined'),
        'message': relationship(Message, lazy='joined'),
        'customfields': relationship(CustomFields),
        }
       )

mapper(Info, t_info,
       inherits=Result,
       polymorphic_identity='info',
       properties={
        'location': relationship(Location, lazy='joined'),
        'message': relationship(Message, lazy='joined'),
        'customfields': relationship(CustomFields),
        }
       )

mapper(Location, t_location,
       properties={
        'file': relationship(File, lazy='joined'),
        #, backref='locations', order_by=t_file.c.abspath)
        'function': relationship(Function, lazy='joined'),
        'point': relationship(Point, lazy='joined'),
        'range_': relationship(Range, lazy='joined'),
        }
       )

mapper(File, t_file,
       properties={
        'hash_': relationship(Hash, lazy='joined'),
        }
       )

mapper(Hash, t_hash)

mapper(Function, t_function)

mapper(Point, t_point)

mapper(Range, t_range,
       properties={
        'start': relationship(Point, foreign_keys=t_range.c.start_id,
                              lazy='joined'),
        'end': relationship(Point, foreign_keys=t_range.c.end_id,
                            lazy='joined')
        # foreign_keys specified to avoid ambiguity
        }
       )

mapper(CustomFields, t_customfields)
