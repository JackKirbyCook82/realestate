# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 2020
@name:   Real Estate Constructor Objects
@author: Jack Kirby Cook

"""

from itertools import product

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Feed', 'Environment']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]
_flatten = lambda nesteditems: [item for items in nesteditems for item in items]


class Feed(object):
    def __init__(self, calculations, renderer, **tables):
        self.__calculations = calculations
        self.__renderer = renderer
        self.__tables = tables

    def __call__(self, *args, geography, **kwargs): 
        dates = set(_filterempty(_aslist(kwargs.pop('date', None)) + _aslist(kwargs.pop('dates', []))))
        return self.__gettables(*args, geography=geography, dates=dates, **kwargs)
       
    def __getitem__(self, key):
        def wrapper(*args, geography, **kwargs): 
            dates = set(_filterempty(_aslist(kwargs.pop('date', None)) + _aslist(kwargs.pop('dates', []))))
            return self.__gettable(self.__tables[key], *args, geography=geography, dates=dates, **kwargs)
        return wrapper

    def __gettables(self, *args, **kwargs):
        return {tableKey:self.__gettable(tableID, *args, **kwargs) for tableKey, tableID in self.__tables.items()}
    
    def __gettable(self, tableID, *args, **kwargs):
        print(self.__renderer(self.__calculations[tableID]), '\n')
        return self.__calculations[tableID](*args, **kwargs)   


class Environment(object):
    @property
    def concepts(self): return self.__concepts   
    @property
    def dimensions(self): return self.__dimensions    
    
    def __init__(self, concepts, **tables): 
        self.__concepts = concepts
        self.__tables = tables
        self.__dimensions = self.__getdimensions(**tables)
    
    def __getdimensions(self, **tables):
        axiskeys = set(_flatten([table.headerkeys for table in tables.values()]))
        axiskeys = [axiskey for axiskey in axiskeys if all([axiskey in table.headers for table in tables.values()])]
        headers = list(tables.values())[0].headers
        return [axiskey for axiskey in axiskeys if all([set(headers[axiskey]) == set(table.headers[axiskey]) for table in list(tables.values())[1:]])]
  
    def iterate(self, *axes):
        assert all([axis in self.dimensions for axis in axes])
        for items in product(*[list(self.__tables.values())[0].headers[axis] for axis in axes]): yield items

    def __getitem__(self, key):
        assert key in self.concepts.keys()
        def wrapper(*args, **kwargs): return self(key, *args, **kwargs)  
        return wrapper  

    def __call__(self, key, *args, **kwargs):
        assert key in self.concepts.keys()
        tables = self.__getTables(self.concepts[key]._fields, *args, **kwargs)
        return self.concepts[key](tables, *args, **kwargs)

    def __getTable(self, field, *args, **kwargs):
        newscope = {key:kwargs[key] for key in self.__tables[field].headerkeys if key in kwargs.keys()}
        table = self.__tables[field].sel(**newscope)
        for scopekey in newscope.keys(): table = table.squeeze(scopekey)
        return table    

    def __getTables(self, fields, *args, **kwargs):
        return {field:self.__getTable(field, *args, **kwargs) for field in _aslist(fields)}




    