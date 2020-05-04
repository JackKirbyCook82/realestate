# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 2020
@name:   Real Estate Constructor Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from itertools import product
from scipy.linalg import cholesky, eigh
from collections import OrderedDict as ODict

from utilities.concepts import concept
from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['createEnvironment', 'Environment', 'Feed', 'MonteCarlo']
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
       
    def __getitem__(self, tableKey):
        def wrapper(*args, geography, **kwargs): 
            dates = set(_filterempty(_aslist(kwargs.pop('date', None)) + _aslist(kwargs.pop('dates', []))))
            return self.__gettable(self.__tables[tableKey], *args, geography=geography, dates=dates, **kwargs)
        return wrapper

    def __gettables(self, *args, **kwargs):
        return {tableKey:self.__gettable(tableID, *args, **kwargs) for tableKey, tableID in self.__tables.items()}
    
    def __gettable(self, tableID, *args, **kwargs):
        print(self.__renderer(self.__calculations[tableID]), '\n')
        return self.__calculations[tableID](*args, **kwargs)   

    def __enter__(self, EnvironmentType, *args, **kwargs): return EnvironmentType(**self(*args, **kwargs))
    def __exit__(self, *args): pass


class Environment(object):
    __concepts = {}
    __functions = {}
    
    @classmethod
    def addconcept(cls, key, fields, function):
        cls.__concepts[key] = concept(key, fields)
        cls.__functions[key] = function
    
    @property
    def dimensions(self): return self.__dimensions    
    def __init__(self, **tables): 
        self.__tables = tables
        self.__dimensions = self.__getdimensions(**tables)
    
    def __getdimensions(self, **tables):
        axiskeys = set(_flatten([table.headerkeys for table in tables.values()]))
        axiskeys = [axiskey for axiskey in axiskeys if all([axiskey in table.headers for table in tables.values()])]
        return [axiskey for axiskey in axiskeys if all([list(tables.values())[0].headers[axiskey] == table.headers[axiskey] for table in list(tables.value())[1:]])]
  
    def iterate(self, *axes):
        assert all([axis in self.dimensions for axis in axes])
        for items in product(*[self.__tables.headers[axis] for axis in axes]): yield items

    def __getitem__(self, conceptKey):
        def wrapper(*args, **kwargs): return self(conceptKey, *args, **kwargs)  
        return wrapper  

    def __call__(self, conceptKey, *args, **kwargs):
        tables = {tableKey:self.__applyFunction(conceptKey, table, *args, **kwargs) for tableKey, table in self.__getTables(conceptKey, *args, **kwargs)}
        return self.__concepts[conceptKey(**tables)]

    def __getTable(self, tableKey, *args, axes=[], axis=None, **kwargs):
        axes = _filterempty(_aslist(axes) + _aslist(axis))
        newscope = {key:kwargs.pop(key) for key in self.__tables[tableKey].headerkeys if key not in _aslist(axes)}
        table = self.__tables[tableKey].sel(**newscope)
        for scopekey in newscope.keys(): table.squeeze(scopekey)
        return table    

    def __getTables(self, tableKeys, *args, **kwargs):
        for tableKey in _aslist(tableKeys): yield tableKey, self.__getTable(tableKey, *args, **kwargs)
      
    def __applyFunction(self, conceptKey, table, *args, **kwargs):
        return self.__functions[conceptKey](table, *args, **kwargs)
 
    
def createEnvironment(name, concepts, functions={}, default=lambda x, *args, **kwargs: x):
    assert isinstance(concepts, dict)
    assert isinstance(functions, dict)
    name = ''.join([uppercase(name), Environment.__name__])
    bases = (Environment,)
    concepts = {key:concept(key, fields) for key, fields in concepts.items()}
    functions = {key:functions.get(key, default) for key in concepts.keys()}
    attrs = {'__concepts':concepts, '__functions':functions}
    return type(name, bases, attrs) 
    

class MonteCarlo(object):
    @property
    def keys(self): return list(self.__histtables.keys())
    
    def __init__(self, **tables):
        self.__tables = ODict([(key, value) for key, value in tables.items()])
        self.__correlationmatrix = np.zero((len(self), len(self)))
        np.fill_diagonal(self.__correlationmatrix, 1)

    def __call__(self, size, *args, **kwargs):
        samplematrix = self.__samplematrix(size, *args, **kwargs)    
        sampletable = {key:list(values) for key, values in zip(self.keys, samplematrix)}
        return pd.DataFrame({sampletable})               
        
    def __samplematrix(self, size, *args, method='cholesky', **kwargs):
        samplematrix = np.array([table(size) for table in self.__tables.values()]) 
        if method == 'cholesky':
            correlation_matrix = cholesky(self.__correlationmatrix, lower=True)
        elif method == 'eigen':
            evals, evecs = eigh(self.__correlationmatrix)
            correlation_matrix = np.dot(evecs, np.diag(np.sqrt(evals)))
        else: raise ValueError(method)
        return np.dot(correlation_matrix, samplematrix).transpose()  








    