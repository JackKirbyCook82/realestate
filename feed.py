# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 2020
@name:   Real Estate Constructor Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from scipy.linalg import cholesky, eigh
from collections import OrderedDict as ODict

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from utilities.concepts import concept
from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Feed', 'MonteCarlo', 'create_environment']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]


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


def create_environment(name, **concepts):    
    name = ''.join([uppercase(name), Environment.__name__])
    bases = (Environment,)
    attrs = {'concepts':{name:concept(name, fields) for name, fields in concepts.items()}}
    return type(name, bases, attrs)    


class Environment(object):
    concepts = {}
    def __init__(self, **tables):    
        self.__geography = list(tables.values())[0].headers['geography'] 
        self.__date = list(tables.values())[0].headers['date']        
        assert all([self.__geography == table.headers['geography'] for table in tables.values()])
        assert all([self.__date == table.headers['date'] for table in tables.values()])
        self.__tables = tables

    def __enter__(self): return self
    def __exit__(self, *args): pass
    
    def __iter__(self): pass

    def __getitem__(self, conceptKey):
        def wrapper(*args, **kwargs):
            fields = self.concepts[conceptKey].fields
            concept =  self.concepts[conceptKey](**{field:self.__getTable(field, *args, axis=field, **kwargs) for field in fields})
        return wrapper

#    def __getTables(self, tableKey, *args, axes=[], axis=None, **kwargs):
#        axes = _filterempty(_aslist(axes) + _aslist(axis))
#        scope = {key:kwargs.pop(key) for key in self.__tables[tableKey].headerkeys if key not in _aslist(axes)}
#        table = self.__tables[tableKey].sel(**scope)
#        for scopekey in scope.keys(): table.squeeze(scopekey)
#        return table            
#    
#    def __getHistogram(self, tableKey, *args, **kwargs): return self.__getTable(tableKey, *args, axis=tableKey, **kwargs).tohistogram(*args, **kwargs)    
#    def __getCurve(self, tableKey, *args, **kwargs): return self.__getTable(tableKey, *args, axis=tableKey, **kwargs).tocurve(*args, **kwargs)         
#    def __getConcept(self, conceptKey, *args, astype='histogram', **kwargs): return self.__getConcept(astype, conceptKey, *args, **kwargs)
#    
#    @keydispatcher
#    def __getconcept(self, conceptType, conceptKey, *args, **kwargs): pass
#    @__getConcept.register('histogram')
#    def __gethistogramconcept(self, conceptKey, *args, **kwargs): return self.concepts[conceptKey](**{field:self.__getHistogram(field, *args, axis=field, **kwargs) for field in self.concept[conceptKey].fields})
#    @__getConcept.register('curve')
#    def __getcurveconcept(self, conceptKey, *args, **kwargs): return self.concepts[conceptKey](**{field:self.__getCurve(field, *args, axis=field, **kwargs) for field in self.concept[conceptKey].fields})
#    @__getConcept.register('array')
#    def __getarrayconcept(self, conceptKey, *args, **kwargs): return self.concepts[conceptKey](**{field:self.__getTables(field, *args, **kwargs) for field in self.concept[conceptKey].fields})


class MonteCarlo(object):
    @property
    def keys(self): return list(self.__histtables.keys())
    
    def __init__(self, **histtables):
        self.__histtables = ODict([(key, value) for key, value in histtables.items()])
        self.__correlationmatrix = np.zero((len(self), len(self)))
        np.fill_diagonal(self.__correlationmatrix, 1)

    def __call__(self, size, *args, **kwargs):
        samplematrix = self.__samplematrix(size, *args, **kwargs)    
        sampletable = {key:list(values) for key, values in zip(self.keys, samplematrix)}
        return pd.DataFrame({sampletable})               
        
    def __samplematirx(self, size, *args, method='cholesky', **kwargs):
        samplematrix = np.array([table(size) for table in self.__tables.values()]) 
        if method == 'cholesky':
            correlation_matrix = cholesky(self.__correlationmatrix, lower=True)
        elif method == 'eigen':
            evals, evecs = eigh(self.__correlationmatrix)
            correlation_matrix = np.dot(evecs, np.diag(np.sqrt(evals)))
        else: raise ValueError(method)
        return np.dot(correlation_matrix, samplematrix).transpose()  








    