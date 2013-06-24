# TODO: use Firehose __hash__ functions instead of hash

from sqlalchemy import and_

from lib.firehose_orm import FH_UNICITY
from lib.firehose_noslots import _string_type # FIXME


def _unique(session, cls, unique_attrs, hashfunc, queryfunc, constructor,
            arg, kw):
    """
    this is from the SQLAlchemy wiki
    http://www.sqlalchemy.org/trac/wiki/UsageRecipes/UniqueObject
    with addition of unique_attrs and u_hash()/u_filter(),
    for the dynmic creation of functions
    """
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(unique_attrs, *arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(cls, unique_attrs, q, *arg, **kw)
            obj = q.first()
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
        cache[key] = obj
        return obj

def _as_unique(session, cls, *args, **kwargs):
    """
    returns a unique Firehose object, regarding to the session
    i.e. new object if it was not present, or old object if a matching is found
    matchings are checked with u_hash() and u_filter(), which use information
    provided in FH_UNICITY (the unique columns for each Firehose object)
    """
    def u_hash(unique_attrs, **kwargs):
        """ hashs the object using its unique columns """
        res = ""
        for arg in kwargs:
            if arg in unique_attrs:
                res += str(hash(kwargs[arg]))
        return res
                
    def u_filter(cls, unique_attrs, query, **kwargs):
        """ gets a SQLAlchemy filter using the class unique columns """
        clauses = []
        for arg in kwargs:
            if arg in unique_attrs:
                clauses.append(getattr(cls, arg) == kwargs[arg])
        # returns and_(Foo.bar1 == bar1, Foo.bar2 == bar2, ...)
        return query.filter(and_(*clauses))
    
    if cls.__name__ in FH_UNICITY.keys(): # we get a unique object
        return _unique(
            session, cls, FH_UNICITY[cls.__name__],
            u_hash, u_filter,
            cls, args, kwargs)
    else:                                 # no need, we create a new object
        return cls(**kwargs)

def get_fh_unique(session, obj):
    def get_attrs(obj):
        """
        returns a tuple (attributename, attribute) for each attribute
        of the Firehose object
        """
        return [(attr.name, getattr(obj, attr.name)) for attr in obj.attrs]
    
    if obj is None:
        return obj
    
    if type(obj) in [int, float, str, _string_type]: # FIXME
        # it's a leave of the Firehose tree, we return it
        return obj
    elif isinstance(obj, list):
        # it's a [nodes] of the Firehose tree, we uniquify each item
        return [get_fh_unique(session, el) for el in obj]
    else:
        # it's a node of the Firehose tree, we uniquify each child
        attrs = get_attrs(obj)
        newattrs = dict()
        # we construct the dict of the uniquified attributes
        for name, attr in attrs:
            newattrs[name] = get_fh_unique(session, attr)
        # and then we construct and return the new parent
        return _as_unique(session, obj.__class__, **newattrs)
    
            
