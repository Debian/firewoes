# Copyright (C) 2013  Matthieu Caneill <matthieu.caneill@gmail.com>
#
# This file is part of Firewose.
#
# Firewose is free software: you can redistribute it and/or modify it under
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


from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, Generator, Sut, Metadata, Message, Location, File, Point, Range, Function
from sqlalchemy import and_



def get_precise_menu(results, filter_, max_number_of_elements=10):
    """
    returns the drill-down menu to precise the search
    An menu item is either:
     - an activated parameter, with its "remove" associated filter
     - a list of possible new parameters, with their "add" filters
    The structure is the following:
    
    [
    (name=attr_name1, type="list", is_sliced=boolean, items=[
        ("foo", nb_occur_foo, foo_filter),
        ("bar", nb_occur_bar, bar_filter),
       ]),
    (name=attr_name2, type="remove", item=("foo", foo_filter)),
    ...
    ]
    """
    
    def get_rm_dict(attr_name):
        """ returns a new filter without attr_name """
        return dict(filter(lambda (x,y): x != attr_name,
                           filter_.iteritems()))
        
    def get_add_dict(attr_name, value):
        """ returns a new filter with attr_name=value in addition """
        newdict = dict(**filter_)
        newdict[attr_name] = value
        return newdict
        
    def get_menu_item(
        attr_name,
        cool_name=None,
        max_items=max_number_of_elements):
            
        """
        constructs a menu item
        If the attr_name is present in the parameters, the it's a "remove"
        Otherwise it's a "list"
        
        Parameters:
        attr_name: the attribute name with which we filter the results
        cool_name: the rendered name for a nice title
        max_items: max number of items displayed in a list
        """
        if cool_name is None:
            cool_name = attr_name.replace("_", " ").capitalize()
        if attr_name in keys:# and filter_[attr_name] != "":
            return dict(
                    name=cool_name,
                    type="remove",
                    item=(filter_[attr_name], get_rm_dict(attr_name))
                    )
        
        else:
            # we get the different items corresponding to this parameter
            # in the results list
            sublist = dict()
            # sublist[item] = number of occurences of this item in results
            for res in results:
                try:
                    elem = getattr(res, attr_name)
                    if elem is not None:
                        try:
                            sublist[elem] += 1
                        except KeyError:
                            sublist[elem] = 1
                except Exception as e:
                        app.logger.info(e)
            sublist_with_links = [
                    (elem, nb_occur, get_add_dict(attr_name, elem))
                    for elem, nb_occur in sublist.iteritems()
                    ]
                
            return dict(
                    name=cool_name,
                    type="list",
                    is_sliced=len(sublist_with_links) > max_items,
                    items=sorted(sublist_with_links,
                                 key=lambda x: x[1],
                                 reverse=True)[:max_items]
                    )

    keys = filter_.keys()
    menu = []
    
    menu.append(get_menu_item("result_type"))
    
    menu.append(get_menu_item("sut_name", cool_name="Package name"))
    
    if "sut_name" in keys:
        menu.append(get_menu_item("sut_version",
                                  cool_name="Package version"))
        
        menu.append(get_menu_item("location_file", cool_name="File"))
        if "location_file" in keys:
            menu.append(get_menu_item("location_function",
                                      cool_name="Function"))
    
    menu.append(get_menu_item("sut_type",
                              cool_name = "Package type"))
    
    menu.append(get_menu_item("generator_name"))
    
    if "generator_name" in keys:
        menu.append(get_menu_item("generator_version"))
        menu.append(get_menu_item("message_text", cool_name="Message"))

    return menu

 # def get_clean_args_from_query(query):
        #     """ when all args are in q, this extracts them """
        #     # query string preprocessing
        #     query = query.replace(",", " ")
        #     query = query.replace(";", " ")
            
        #     args = query.split()
        #     clean_args = []

        #     for arg in args:
        #         try:
        #             name, value = arg.split(":")
        #             clean_args.append((name, value))
        #         except: pass

        #     return clean_args
            
def get_filter_clauses_from_clean_args(args):
    """
    returns the filter and the clauses corresponding to
    the given args
    """
    filter_ = dict()
    clauses = []
    keys = [name for (name, value) in args]
    
    # we check the parameters, and:
    # - add the right clauses for retrieving the results
    # - add it in filter_ for later use
    for (name, value) in args:
        #if value != "":
        if name == "sut_name":
            clauses.append(Sut.name == value)
            filter_["sut_name"] = value
        
        elif name == "sut_version" and "sut_name" in keys:
            # sut.version only avaiblable if sut.name exists
            clauses.append(Sut.version == value)
            filter_["sut_version"] = value
            
        elif name == "sut_type":
            clauses.append(Sut.type == value)
            filter_["sut_type"] = value
            
        elif name == "sut_type":
            clauses.append(Sut.type == value)
            filter_["sut_type"] = value
                    
        elif name == "generator_name":
            clauses.append(Generator.name == value)
            clauses.append(Metadata.generator_id == Generator.id)
            filter_["generator_name"] = value
                    
        elif (name == "generator_version"
              and "generator_name" in keys):
            # generator.version only avaiblable if generator.name
            clauses.append(Generator.version == value)
            filter_["generator_version"] = value
            
        elif name == "result_type":
            clauses.append(Result.type == value)
            filter_["result_type"] = value
            
        elif name == "message_text" and "generator_name" in keys:
            clauses.append(Message.text == value)
            filter_["message_text"] = value
                    
          # TODO: issue.cwe
        elif name == "location_file" and "sut_name" in keys:
            clauses.append(Location.file_id == File.id)
            clauses.append(File.givenpath == value)
            filter_["location_file"] = value

        elif name == "location_function" and "location_file" in keys:
            clauses.append(Location.function_id == Function.id)
            clauses.append(Function.name == value)
            filter_["location_function"] = value
                    
    return filter_, clauses

def make_q(session, class_, clauses):
    """ returns a request for a result (issue/failure/info) """
    return (session.query(
                class_.id,
                Result.type.label("result_type"),
                File.givenpath.label("location_file"),
                Function.name.label("location_function"),
                Message.text.label("message_text"),
                Message.id.label("message_id"),
                Point, Range,
                Sut.name.label("sut_name"),
                Sut.version.label("sut_version"),
                Sut.type.label("sut_type"),
                Generator.name.label("generator_name"),
                Generator.version.label("generator_version"))
            .outerjoin(Location, File, Function, Point, Analysis,
                       Metadata, Generator, Sut, Message)
            .outerjoin(Range, and_( # TOTEST
                            Range.start_id==Point.id, Range.end_id==Point.id))
            .filter(*clauses))
