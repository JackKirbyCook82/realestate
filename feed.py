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

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Feed', 'Environment', 'MonteCarlo']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]


class FeedNotCalculatedError(Exception): pass
class InconsistentEnvironmentError(Exception): pass


class Feed(object):    
    @property
    def name(self): return self.__name
    @property
    def calculated(self): return self.__calculated
    
    def __repr__(self): return '{}(name={}, calculation={}, renderer={})'.format(self.__class__.__name__, self.__name, repr(self.__calculations), repr(self.__renderer))  
    def __init__(self, name, calculation, renderer, **tables): 
        self.__name = name
        self.__calculation = calculation
        self.__renderer = renderer
        self.__queue = tables
        self.__tables = {}
        self.__calculated = False

    def calculate(self, *args, geography, dates, **kwargs):
        dates = _filterempty(_aslist(dates) + _aslist(kwargs.pop('date', [])))
        for tableKey, tableID in self.__queue.items():
            print(self.__renderer(self.__calculations[tableID]))
            self.__tables[tableKey] = self.__calculations[tableID](*args, geography=geography, dates=dates, **kwargs)
        self.__calculated = True

    def __call__(self, *args, geography, date=None, **kwargs):
        if not self.calculated: raise FeedNotCalculatedError(repr(self))
        tables = {tableKey:table.sel(geography=geography).squeeze('geography') for tableKey, table in self.__tables.items()}
        if date: tables = {tableKey:table.sel(date=date).squeeze('date') for tableKey, table in tables.items()}    
        return {tableKey:table.tohistogram() for tableKey, table in tables.items()}


class Environment(object):   
    @property
    def name(self): return self.__name
    @property
    def geography(self): return self.__geographuy
    @property
    def date(self): return self.__date
    
    def __repr__(self): return '{}(name={}, geography={}, date={})'.format(self.__class__.__name__, self.__name, repr(self.__geography), repr(self.__date))  
    def __init__(self, name, **tables): 
        self.__name, self.__tables = name, tables
        self.__geography, self.__date = list(tables.values())[0].scope['geography'], list(tables.values())[0].scope['date'] 
        if not all([table.scope['geography'] == self.__geography for table in tables.values()]): raise InconsistentEnvironmentError(repr(self))
        if not all([table.scope['date'] == self.__date for table in tables.values()]): raise InconsistentEnvironmentError(repr(self))
        

class MonteCarlo(object):
    @property
    def name(self): return self.__name
    @property
    def keys(self): return list(self.__histtables.keys())
    
    def __init__(self, name, **histtables):
        self.__name = name
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
    
    











    