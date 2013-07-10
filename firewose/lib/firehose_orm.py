#   Copyright 2013 David Malcolm <dmalcolm@redhat.com>
#   Copyright 2013 Red Hat, Inc.
#   Copyright 2013 Matthieu Caneill <matthieu.caneill@gmail.com>
#   
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
#   You should have received a copy of the GNU Lesser General Public
#   License along with this library; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301
#   USA


from sqlalchemy import Table, MetaData, Column, \
    ForeignKey, Integer, String, Float, ForeignKeyConstraint, \
    event, DDL, Index
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
    #Analysis = ("metadata", "customfields"),
    Generator = ("name", "version"),
    Metadata = ("sut", "file_", "stats"),
    Stats = ("wallclocktime"),
    #Sut = ("type", "name", "version", "release", "buildarch"),
    SourceRpm = ("name", "version", "release", "buildarch"),
    DebianBinary = ("name", "version", "release", "buildarch"),
    DebianSource = ("name", "version", "release"),
    #Result = ("analysis_id", "type"),
    #Issue = ("cwe", "testid", "severity", "message", "notes", "location",
    #         "trace", "customfields"),
    #Failure = ("failureid", "location", "message", "customfields"),
    #Info = ("infoid", "location", "message", "customfields"),
    Message = ("text"),
    Notes = ("text"),
    #Trace = ("states"),
    State = ("location", "notes"),
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
Index('ix_generator_name_version', t_generator.c.name, t_generator.c.version)

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
Index('ix_metadata_wallclocktime', t_stats.c.wallclocktime)

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
Index('ix_sut_name_version_release_buildarch',
      t_sut.c.name,
      t_sut.c.version,
      t_sut.c.release,
      t_sut.c.buildarch)

# For the Result hierarchy we use joined-table inheritance
t_result = \
    Table('result', metadata,
          Column('id', Integer, primary_key=True), # renamed from result_id
          Column('analysis_id', Integer,
                 ForeignKey('analysis.id'), nullable=False),
          Column('type', String(10), nullable=False),
          )
Index('ix_result_type', t_result.c.type)

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
Index('ix_issue_testid', t_issue.c.testid)
Index('ix_issue_message_id', t_issue.c.message_id)
Index('ix_issue_location_id', t_issue.c.location_id)

t_failure = \
    Table('failure', metadata,
          Column('result_id', Integer,
                 ForeignKey('result.id'), primary_key=True),
          Column('failureid', String),
          Column('location_id', Integer, ForeignKey('location.id')),
          Column('message_id', Integer, ForeignKey('message.id')),
          Column('customfields_id', Integer, ForeignKey('customfields.id')),
          )
Index('ix_failure_failureid', t_failure.c.failureid)
Index('ix_failure_location_id', t_failure.c.location_id)
Index('ix_failure_message_id', t_failure.c.message_id)

t_info = \
    Table('info', metadata,
          Column('result_id', Integer,
                 ForeignKey('result.id'), primary_key=True),
          Column('infoid', String),
          Column('location_id', Integer, ForeignKey('location.id')),
          Column('message_id', Integer, ForeignKey('message.id')),
          Column('customfields_id', Integer, ForeignKey('customfields.id')),
          )
Index('ix_info_infoid', t_info.c.infoid)
Index('ix_info_location_id', t_info.c.location_id)
Index('ix_info_message_id', t_info.c.message_id)

t_message = \
    Table('message', metadata,
          Column('id', Integer, primary_key=True),
          Column('text', String),
          )
Index('ix_message_text', t_message.c.text)

t_notes = \
    Table('notes', metadata,
          Column('id', Integer, primary_key=True),
          Column('text', String),
          )
Index('ix_notes_text', t_notes.c.text)

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
Index('ix_state_trace_id', t_state.c.trace_id)

t_location = \
    Table('location', metadata,
          Column('id', Integer, primary_key=True),
          Column('file_id', Integer, ForeignKey('file.id'), nullable=False),
          Column('function_id', Integer, ForeignKey('function.id')),
          # either a point or a range:
          Column('point_id', Integer, ForeignKey('point.id')),
          Column('range_id', Integer, ForeignKey('range.id')),
          )
Index('ix_location_file_id_function_id',
      t_location.c.file_id,
      t_location.c.function_id)

t_file = \
    Table('file', metadata,
          Column('id', Integer, primary_key=True),
          Column('givenpath', String, nullable=False),
          Column('abspath', String),
          Column('hash_id', Integer, ForeignKey('hash.id')),
          )
Index('ix_file_givenpath', t_file.c.givenpath)

t_hash = \
    Table('hash', metadata,
          Column('id', Integer, primary_key=True),
          Column('alg', String, nullable=False),
          Column('hexdigest', String, nullable=False),
          )
Index('ix_hash_hexdigest', t_hash.c.hexdigest)

t_function = \
    Table('function', metadata,
          Column('id', Integer, primary_key=True),
          Column('name', String, nullable=False),
          )
Index('ix_function_name', t_function.c.name)

t_point = \
    Table('point', metadata,
          Column('id', Integer, primary_key=True),
          Column('line', Integer, nullable=False),
          Column('column', Integer, nullable=False),
          )
Index('ix_point_line_column', t_point.c.line, t_point.c.column)

t_range = \
    Table('range', metadata,
          Column('id', Integer, primary_key=True),
          Column('start_id', Integer,
                 ForeignKey('point.id'), nullable=False),
          Column('end_id', Integer,
                 ForeignKey('point.id'), nullable=False),
          )
Index('ix_range_start_id_end_id', t_range.c.start_id, t_range.c.end_id)

t_customfields = \
    Table('customfields', metadata,
          Column('id', Integer, primary_key=True))

t_intfield = \
    Table('intfield', metadata,
          Column('id', Integer, primary_key=True),
          Column('customfields_id', Integer,
                 ForeignKey('customfields.id'), nullable=False),
          Column('name', String, nullable=False),
          Column('value', Integer, nullable=False),
          )
Index('ix_intfield_name', t_intfield.c.name)

t_strfield = \
    Table('strfield', metadata,
          Column('id', Integer, primary_key=True),
          Column('customfields_id', Integer,
                 ForeignKey('customfields.id'), nullable=False),
          Column('name', String, nullable=False),
          Column('value', String, nullable=False),
          )
Index('ix_strfield_name', t_strfield.c.name)

############################################################################
# Mappers
############################################################################

mapper(Analysis, t_analysis,
       properties={
        'metadata': relationship(Metadata, lazy='joined'),
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

mapper(SourceRpm,
       inherits=sut_mapper,
       polymorphic_identity='source-rpm')

mapper(DebianBinary,
       inherits=sut_mapper,
       polymorphic_identity='debian-binary')

mapper(DebianSource,
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
