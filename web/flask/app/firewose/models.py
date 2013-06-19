from lib.firehose_orm import Analysis, Issue, Failure, Info, Result, Generator, Sut, Metadata, Message, Location, File, Point, Range, Function
from sqlalchemy import and_

from app import session, app


### EXCEPTIONS ###

class Http500Error(Exception): pass
class Http404Error(Exception): pass


### MODEL CLASSES ###


def to_dict(elem):
    """
    serializes a SQLAchemy response into a dict
    /!\ backrefs are followed and can do infinite recursion TODO
    """
    if elem is None:
        return None
    elif type(elem) in [int, float, str, unicode, bool]:#_string_type]
        return elem
    
    elif isinstance(elem, list):
        return [to_dict(e) for e in elem]
    elif isinstance(elem, tuple): # KeyedTuple (queries with specified columns)
        res = dict()
        elem = elem._asdict()
        for attr_name in elem:
            res[attr_name] = to_dict(elem[attr_name])
        return res
    else:
        res = dict()
        cls = type(elem)
        for attr_name in cls._sa_class_manager.local_attrs:
                attr = getattr(elem, attr_name)
                #if type(attr) in [int, float, str, unicode]:#_string_type]
                #    res[attr_name] = attr
                #else:
                res[attr_name] = to_dict(attr)
        return res


class FHGeneric(object):
    def all(self):
        elem = session.query(self.fh_class).all()
        return to_dict(elem)
    
    def id(self, id):
        try:
            elem = session.query(self.fh_class).filter(
                self.fh_class.id == id).first()
        except:
            raise Http500Error
        
        try:
            id = elem.id # raises error if the element doesn't exist
        except:
            raise Http404Error("This element (%s, %i) doesn't exist."
                               % (self.fh_class.__name__, id))
        return to_dict(elem)

class Generator_app(FHGeneric):
    def __init__(self):
        self.fh_class = Generator

    def all(self):
        elem = session.query(self.fh_class).order_by(Generator.name).all()
        return to_dict(elem)
    
    def unique_by_name(self):
        elem = session.query(Generator.name).distinct().all()
        return to_dict(elem)
    
    def versions(self, name):
        elem = session.query(Generator.version).filter(
            Generator.name == name).all()
        return to_dict(elem)

class Analysis_app(FHGeneric):
    def __init__(self):
        self.fh_class = Analysis

    def all(self):
        elem = session.query(Analysis.id,
                             Generator.name.label("generator_name")).filter(
            and_(Analysis.metadata_id == Metadata.id,
                 Metadata.generator_id == Generator.id)).all()
        return to_dict(elem)

    def id(self, id):
        elem = session.query(Analysis).filter(Analysis.id == id).first()
        elem = to_dict(elem)
        elem['results'] = to_dict(session.query(
                Result.id).filter(Result.analysis_id == id).all())
        return elem

class Sut_app(FHGeneric):
    def __init__(self):
        self.fh_class = Sut
        
    def versions(self, name):
        elem = session.query(Sut.version).filter(
            Sut.name==name).order_by(Sut.version).all()
        return to_dict(elem)

class Result_app(FHGeneric):
    def __init__(self):
        self.fh_class = Result
        
    def all(self):
        elem = session.query(Result.id).all()
        return to_dict(elem)
    
    def _get_precise_menu(self, results, filter_):
        """
        returns the drill-down menu to precise the search
        An menu item is either:
          - an activated parameter, with its "remove" associated filter
          - a list of possible new parameters, with their "add" filters
        The structure is the following:
        
        [
            (attr_name1, "list", [
                    ("foo", foo_filter),
                    ("bar", bar_filter),
                    ]),
            (attr_name2, "remove", ("foo", foo_filter)),
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
        
        def get_menu_item(attr_name, cool_name=None):
            """
            constructs a menu item
            If the attr_name is present in the parameters, the it's a "remove"
            Otherwise it's a "list"
            """
            if cool_name is None:
                cool_name = attr_name.replace(".", " ").capitalize()
            if attr_name in keys:# and filter_[attr_name] != "":
                return (
                    (cool_name,
                     "remove",
                     (filter_[attr_name], get_rm_dict(attr_name))
                     )
                    )
            else:
                # we get the different items corresponding to this parameter
                # in the results list
                sublist = set()
                for res in results:
                    try:
                        elem = getattr(res, attr_name)
                        if elem is not None:
                            sublist.add(elem)
                    except Exception as e:
                        app.logger.info(e)
                sublist_with_links = [(elem, get_add_dict(attr_name, elem))
                                      for elem in sublist]
                
                return (
                    (cool_name,
                     "list",
                     sublist_with_links,
                     )
                    )

        keys = filter_.keys()
        menu = []
        
        menu.append(get_menu_item("result.type"))

        menu.append(get_menu_item("sut.name", cool_name="Package name"))
        
        if "sut.name" in keys:
            menu.append(get_menu_item("sut.version",
                                      cool_name="Package version"))
            menu.append(get_menu_item("location.file", cool_name="File"))
            if "location.file" in keys:
                menu.append(get_menu_item("location.function",
                                          cool_name="Function"))
        
        menu.append(get_menu_item("generator.name"))
        
        if "generator.name" in keys:
            menu.append(get_menu_item("generator.version"))
            
        menu.append(get_menu_item("message.text", cool_name="Message"))

        return menu
    
    def filter(self, request_args):
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
            returns the filter and the clauses correponding to
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
                if name == "sut.name":
                    clauses.append(Sut.name == value)
                    filter_["sut.name"] = value
                    
                elif name == "sut.version" and "sut.name" in keys:
                    # sut.version only avaiblable if sut.name exists
                    clauses.append(Sut.version == value)
                    filter_["sut.version"] = value
                    
                elif name == "sut.release":
                    clauses.append(Sut.release == value)
                    filter_["sut.release"] = value
                    
                elif name == "sut.type":
                    clauses.append(Sut.type == value)
                    filter_["sut.type"] = value
                    
                elif name == "generator.name":
                    clauses.append(Generator.name == value)
                    clauses.append(Metadata.generator_id == Generator.id)
                    filter_["generator.name"] = value
                    
                elif (name == "generator.version"
                      and "generator.name" in keys):
                    # generator.version only avaiblable if generator.name
                    clauses.append(Generator.version == value)
                    filter_["generator.version"] = value
                    
                elif name == "result.type":
                    clauses.append(Result.type == value)
                    filter_["result.type"] = value
                    
                elif name == "message.text":
                    clauses.append(Message.text == value)
                    filter_["message.text"] = value
                    
                    # TODO: issue.cwe
                elif name == "location.file" and "sut.name" in keys:
                    clauses.append(Location.file_id == File.id)
                    clauses.append(File.givenpath == value)
                    filter_["location.file"] = value

                elif name == "location.function" and "location.file" in keys:
                    clauses.append(Location.function_id == Function.id)
                    clauses.append(Function.name == value)
                    filter_["location.function"] = value
                    
            return filter_, clauses

        
        def make_q(class_, clauses):
            """ returns a request for a result (issue/failure/info) """
            return (session.query(
                    class_.id,
                    Result.type.label("result.type"),
                    File.givenpath.label("location.file"),
                    Function.name.label("location.function"),
                    Message.text.label("message.text"),
                    Message.id.label("message.id"),
                    Point, Range,
                    Sut.name.label("sut.name"),
                    Sut.version.label("sut.version"),
                    Generator.name.label("generator.name"),
                    Generator.version.label("generator.version"))
                    .outerjoin(Location)
                    .outerjoin(File)
                    .outerjoin(Function)
                    .outerjoin(Point)
                    .outerjoin(Range, and_( # TOTEST
                        Range.start_id==Point.id, Range.end_id==Point.id))
                    .outerjoin(Analysis)
                    .outerjoin(Metadata)
                    .outerjoin(Generator)
                    .outerjoin(Sut)
                    .outerjoin(Message)
                    .filter(*clauses))
        
        if "q" in request_args.keys():
            # /search?q=sut.name:hello%20sut.version:blabla...
            clean_args = get_clean_args_from_query(request_args["q"])
        else:
            # /search?sut.name=hello&sut.version=blabla...
            clean_args = [(name, value) for name, value
                          in request_args.iteritems()]

        filter_, clauses = get_filter_clauses_from_clean_args(clean_args)
        
        # TODO: polymorphism?
        q_issue = make_q(Issue, clauses)
        q_failure = make_q(Failure, clauses)
        q_info = make_q(Info, clauses)
        results = q_issue.union(q_failure, q_info).all()
        
        precise_menu = self._get_precise_menu(results, filter_)

        return (to_dict(results), filter_, precise_menu)

    def id(self, id, with_metadata=True):
        if not(with_metadata):
            return super(Result_app, self).id(id)
        else:
            elem = session.query(Result, Metadata).filter(and_(
                    Result.id == id,
                    Result.analysis_id == Analysis.id,
                    Analysis.metadata_id == Metadata.id)).first()
            return to_dict(elem)
