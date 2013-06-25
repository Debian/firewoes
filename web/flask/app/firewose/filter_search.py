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


from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, \
    Generator, Sut, Metadata, Message, Location, File, Point, Range, Function
from sqlalchemy import and_


# Dependencies for the filter arguments
# e.g. sut_version is only displayed when sut_name is chosen
filter_dependencies = dict(
    sut_version = ["sut_name"],
    location_file = ["sut_name"],
    location_function = ["location_file", "sut_name"],
    generator_version = ["generator_name"],
    message_text = ["generator_name"],
    )

def check_dependency(arg, args):
    """
    returns true if the dependencies of arg are satisfied by args
    """
    for dep in filter_dependencies.get(arg) or []:
        if dep not in args:
            return False
    return True

class FilterArgs(object):
    """
    A wrapper for the filter arguments
    """
    def __init__(self, args):
        """
        args: dictionary of arguments, e.g. request.args
        only the arguments whose dependencies are satisfied are kept
        """
        self.args = dict((x, y) for x, y in args.iteritems()
                         if check_dependency(x, args))
        
    def with_add_arg(self, arg, value):
        """
        returns the current filter with an added argument
        """
        args = dict(**self.args)
        args[arg] = value
        return args
    
    def with_remove_arg(self, arg):
        """
        returns the current filter with a deleted argument
        """
        return dict((x, y) for (x, y) in self.args.iteritems() if x != arg)
    
    def get(self, key):
        """
        returns the argument whose name is key, or None if it's not found
        """
        return self.args.get(key)
    
    def get_all(self):
        """
        returns all the arguments in a dict
        """
        return self.args

class DrillDownMenu(object):
    """
    A drill-down menu
    Its composed of a list of DrillDownItems
    """
    def __init__(self, filter_):
        """
        filter_: a FilterArgs
        """
        self.filter_ = filter_
        self.items = []
        
    def get_clauses(self):
        """
        returns the clauses used to filter a query to Result
        """
        clauses = []
        for item in self.items:
            clauses += item.get_clauses()
        return clauses
    
    def get_menu_items(self, results, limit=None):
        """
        Returns the items for the menu, in the form:
        [
        dict(active=true,                 # it's an already selected item
             remove_filter=dict(...),     # the 'remove' link
             name=foo,                    # name, e.g. sut_name
             value=bar),                  # value, e.g. python-ethtool
             
        dict(active=false,                # this item has not be chosen yet
             items=[                      # list of subitems
               dict(add_filter=dict(...), # dict to add the subitem in args
                    count=42,             # number of occurences
                    name=foo),            # name, e.g. python-ethtool
               ...]
             name=foo,                    # name, e.g. sut_name
             is_sliced=bool),             # if the list has been sliced
         ...
        ]
        
        Arguments:
        results: list of Result in where to extract the information
        limit: slice the subitems
        """
        inactive_items = [item for item in self.items if not item.is_active()]
        for res in results:
            for item in inactive_items:
                try:
                    item.add_subitem(res[item.get_name()])
                except: pass
        return [submenu.get_menu_item(self.filter_, limit=limit)
                for submenu in self.items]
    
    def add_submenu(self, name, fh_attr=None, add_clauses=[], cool_name=None):
        """
        adds a DrillDownItem in this menu
        
        Arguments:
        name: name of the item (e.g. sut_name)
        fh_attr: corresponding Firehose attribute (e.g. Sut.name)
        add_clauses: for special items, we need to add clauses in the query
        cool_name: name to use in rendering
        """
        if check_dependency(name, self.filter_.get_all()):
            self.items.append(DrillDownItem(name,
                                            value=self.filter_.get(name),
                                            add_clauses=add_clauses,
                                            fh_attr=fh_attr,
                                            cool_name=cool_name))

class DrillDownItem(object):
    """
    A submenu of a DrillDownMenu, it can be:
      - active: its argument is set (e.g. the user has chosen to filter
                                     sut_name=python-ethtool)
      - inactive: the user can choose the desired argument
    """
    def __init__(self, name, value=None, add_clauses=[], fh_attr=None,
                 cool_name=None):
        """
        Arguments:
        name: name of the item, e.g. sut_name
        value: if None, the item is inactive, else it's active with value as
               selected argument
        add_clauses: to add other clauses in the query, useful for certain items
        fh_attr: the corresponding Firehose attribute, e.g. Sut.name
        cool_name: name to use for rendering
        """
        self.name = name
        if cool_name is None:
            self.cool_name = name.replace("_", " ").capitalize()
        else:
            self.cool_name = cool_name
        self.value = value
        if self.is_active():
            self.clauses = [fh_attr == value]
            self.clauses += add_clauses
        self.subitems = dict()
        
    def get_clauses(self):
        """
        returns the SQLAlchemy clauses corresponding to this item
        """
        if self.is_active():
            return self.clauses
        else:
            return []

    def get_name(self):
        """ name of the item """
        return self.name
    
    def is_active(self):
        """ true if it's an active item, false otherwise """
        return self.value is not None
    
    def add_subitem(self, subitem):
        """
        For inactive item, adds a subitem (with the count, to sort 
        pertinently the subitems later
        """
        if not self.is_active():
            try:
                self.subitems[subitem] += 1
            except:
                self.subitems[subitem] = 1
        else:
            raise Exception("You can't add subitems to an active submenu")
        
    def get_menu_item(self, filter_, limit=None):
        """
        Returns the menu corresponding to this item
        """
        if self.is_active():
            return dict(name=self.cool_name, value=self.value, active=True,
                        remove_filter=filter_.with_remove_arg(self.name))
        else:
            subitems_with_filters = []
            # we sort and slice the subitems, then construct the dict
            for item in sorted(self.subitems,
                               key=lambda x: self.subitems[x],
                               reverse=True)[:limit]:
                subitems_with_filters.append(
                    dict(name=item,
                         count=self.subitems[item],
                         add_filter=filter_.with_add_arg(self.name, item)))
            
            return dict(name=self.cool_name,
                        items=subitems_with_filters,
                        active=False,
                        is_sliced=(limit < len(self.subitems)))

def create_menu(filter_):
    """
    Returns the Firewose drill down menu
    
    Arguments:
    filter_: a FilterArgs
    """
    menu = DrillDownMenu(filter_)
    
    menu.add_submenu("result_type", Result.type)
    menu.add_submenu("sut_type", Sut.type, cool_name="Package type")
    menu.add_submenu("sut_name", Sut.name, cool_name="Package name")
    menu.add_submenu("sut_version", Sut.version, cool_name="Package version")
    menu.add_submenu("location_file", File.givenpath, cool_name="File",
                     add_clauses=[Location.file_id == File.id])
    menu.add_submenu("location_function", Function.name, cool_name="Function",
                     add_clauses=[Location.function_id == Function.id])
    menu.add_submenu("generator_name", Generator.name,
                     add_clauses=[Metadata.generator_id == Generator.id])
    menu.add_submenu("generator_version", Generator.version)
    menu.add_submenu("message_text", Message.text, cool_name="Message")
    
    return menu

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
