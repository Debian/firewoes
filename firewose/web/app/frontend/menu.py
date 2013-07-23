class Menu(object):
    """
    A menu is a set of active and inactive filters.
    It permits to obtain a drill-down menu, as long as an SQLAlchemy
    filter to query the results.
    """
    def __init__(self, active_filters_dict):
        """
        Creates a menu.
        The active_filter_dict contains the already activated filters,
        in the form name=value, e.g. generator_name="coccinelle".
        """
        self.filters = []
        # we create the active filters
        for key in active_filters_dict.keys():
            for filter_ in all_filters:
                if filter_[0] == key:
                    self.filters.append(filter_[1](
                            value=active_filters_dict[key], active=True))
                    break
        
        # and now the inactive filters:
        for filter_ in all_filters:
            if filter_[0] not in active_filters_dict.keys():
                inactive_filter = filter_[1](active=False)
                if inactive_filter.is_relevant(
                    active_keys=active_filters_dict.keys()):
                    self.filters.append(inactive_filter)
    
    def get_sqla_filter(self, query):
        """
        Filters the query by all active filters, and returns a new
        SQLAlchely query.
        """
        for filter_ in self.filters:
            if filter_.is_active():
                query = filter_.sqla_filter(query)
    
    def __repr__(self):
        string = "MENU:\n"
        for filter_ in self.filters:
            string += "  " + filter_.__repr__() + "\n"
        return string

class Filter(object):
    def __init__(self, value=None, active=False):
        """
        Creates a new filter.
        value is its value in case active=True
        """
        self.value = value
        self.active = active
        if not active:
            self.items = []
    
    def sqla_filter(self, query):
        """
        Filters the SQLAlchemy query.
        """
        # query.filter/filter_by/...
        return query
    
    def get_items(self, query):
        """
        Returns the subitems of the menu (only for inactive filters).
        """
        return None
    
    def is_relevant(self, active_keys=None):
        """
        Returns True if the filter must be used in this context.
        For filters which implement this, should return False if a
        dependency is not satisfied (e.g. generator_version depends on
        generator_name)
        """
        return True
    
    def is_active(self):
        return self.active
    
    def __repr__(self):
        string = self.__class__.__name__ + ":\n"
        string += "    active: " + str(self.active) + "\n"
        if not self.active:
            string += "    items: "
            for item in self.items:
                string += item
            
        return string

class FilterGeneratorName(Filter):
    pass

class FilterGeneratorVersion(Filter):
    pass



all_filters = [
    ("generator_name", FilterGeneratorName),
    ("generator_version", FilterGeneratorVersion),
    ]



if __name__ == "__main__":
    menu = Menu(dict(generator_name="coccinelle"))
    print(menu)
