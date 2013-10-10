# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewoes.
#
# Firewoes is free software: you can redistribute it and/or modify it under
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


import hashlib
from firehose.model import _string_type

def strhash(string):
    """
    Returns the cryptographic hash of a string.
    This allows to easily change the hash algorithm.
    """
    return hashlib.sha1(string).hexdigest()

def get_attrs(obj):
    """
    For a Firehose object, returs a list of tuples (attribute_name, attribute)
    for each of its nodes
    """
    return [(attr.name, getattr(obj, attr.name)) for attr in obj.attrs]

def idify(obj, debug=False):
    """
    Performs a bottom-up browsing of a Firehose tree, to add to each
    object its id, which is its cryptographic hash.
    Acts recursively.
    Returns a tuple: (object_with_id, object_id(=object_hash))
    
    The hash is calculated with the concatenation of node's children, e.g.:
        hash(Generator) =
        hash("name [Generator.name.hash] version [Generator.version.hash]")
    """
    def hashtoken(attr_name, obj_tuple):
        """
        Returns the string chunk used to hash a tree node, e.g.:
        hashtoken("Generator", (Generator(foobar), "54fd24ec..."))
             = "Generator 54fd24ec"
        """
        return attr_name + " " + obj_tuple[1] + " "
    
    if debug:
        print("ENTERING " + str(obj)[:60])
    
    if obj is None:
        return (None, strhash(""))
    
    elif type(obj) in [int, float, str, _string_type]:
        return (obj, strhash(str(obj)))
    
    elif isinstance(obj, list):
        result = [idify(item) for item in obj]
        return result
    
    else:
        objhash = ""
        for (attr_name, attr) in get_attrs(obj):
            res = idify(attr)
            if debug:
                print("SETATTR %s // %s" % (str(obj)[:40], attr_name))
            
            if isinstance(res, list):
                # we get the objects:
                items_without_hashes = [item[0] for item in res]
                # we add their hashes:
                for item in res:
                    objhash += hashtoken(attr_name, item)
                
                # and we update the attribute:
                setattr(obj, attr_name, items_without_hashes)
            else:
                # we add the hash:
                objhash += hashtoken(attr_name, res)
                
                # and update the attribute:
                setattr(obj, attr_name, res[0])
        
        # final hash is the id:
        obj.id = strhash(objhash)
        
        return (obj, obj.id)

def uniquify(session, obj, debug=False):
    """
    Renders a Firehose tree unique, regarding an SQLAlchemy session.
    Inspired by http://www.sqlalchemy.org/trac/wiki/UsageRecipes/UniqueObject
    """
    if debug:
        print("UNIQUIFY: %s" % str(obj)[:60])
    
    # we kep objetcs in cache for better performances
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}
    
    key = (obj.__class__, obj.id)
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            res = (session.query(obj.__class__)
                   .filter(obj.__class__.id == obj.id).first())
            if not res:
                # the object doesn't exist in the db,
                # we check recursively its attributes and add it
                res = obj
                
                # recursion
                for (attr_name, attr) in get_attrs(res):
                    if isinstance(attr, list):
                        # if it's a list we do this for each item
                        setattr(res,
                                attr_name,
                                [uniquify(session, item) for item in attr])
                            
                    elif (type(attr) not in (int, float, str, _string_type)
                          and attr is not None):
                        setattr(res, attr_name, uniquify(session, attr))
                
                # we finally add it
                session.add(res)
        # update the cache
        cache[key] = res
        
        return res
