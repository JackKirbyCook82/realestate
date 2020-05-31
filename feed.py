# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 2020
@name:   Real Estate Constructor Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from numbers import Number
from itertools import product
from scipy.linalg import cholesky, eigh
from collections import OrderedDict as ODict

from tables.tables import EmptyHistArrayError
from utilities.dispatchers import clstype_singledispatcher as typedispatcher

from realestate.economy import Rate

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Feed', 'Data', 'Environment', 'MonteCarlo']
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


class Data(object):
    @property
    def axes(self): return self.__axes
    
    def __init__(self, **tables): self.__tables, self.__axes = tables, self.__getaxes(**tables)
    def __getaxes(self, **tables):
        axiskeys = set(_flatten([table.headerkeys for table in tables.values()]))
        axiskeys = [axiskey for axiskey in axiskeys if all([axiskey in table.headers for table in tables.values()])]
        headers = list(tables.values())[0].headers
        return [axiskey for axiskey in axiskeys if all([set(headers[axiskey]) == set(table.headers[axiskey]) for table in list(tables.values())[1:]])]

    def iterate(self, *axes):
        assert all([axis in self.__axes for axis in axes])
        for items in product(*[list(self.__tables.values())[0].headers[axis] for axis in axes]): yield items
          
    def __getitem__(self, key):
        assert key in self.__tables.keys()
        def wrapper(*args, **kwargs): return self(*args, key=key, **kwargs)
        return wrapper
    
    def __call__(self, *args, key=None, **kwargs):
        if not key: return {key:self.__gettable(key, *args, **kwargs) for key in self.__tables.keys()} 
        else: return self.__gettable(key, *args, **kwargs)        
        
    def __gettable(self, key, *args, **kwargs):        
        newscope = {axis:kwargs[axis] for axis in self.__tables[key].headerkeys if axis in kwargs.keys()}
        table = self.__tables[key].sel(**newscope)
        for scopekey in newscope.keys(): table = table.squeeze(scopekey)
        return table         
        

class Environment(object):
    __counttables = ('households', 'structures', 'population')
    __ratetables = ('discountrate', 'incomerate', 'wealthrate', 'valuerate', 'rentrate')
    
    @property
    def geography(self): return self.__geography
    @property
    def date(self): return self.__date
    
    @property
    def counts(self): return self.__counts
    @property
    def rates(self): return self.__rates
    @property
    def histograms(self): return self.__histograms
    @property
    def concepts(self): return self.__concepts
    
    def __init__(self, geography, date, *args, tables, concepts={}, basis, **kwargs):
        assert isinstance(tables, dict) and isinstance(concepts, dict)
        assert not any([key in tables.keys() for key in concepts.keys()])
        assert all([table.scope['geography'][()] == geography for table in tables.values()])
        self.__geography, self.__date = geography, date
        
        self.__histograms = {}
        for tablekey, table in tables.items():
            if tablekey not in (*self.__ratetables, *self.__counttables):
                try: self.__histograms[tablekey] = self.__gethistogram(table, date, *args, **kwargs)
                except EmptyHistArrayError: self.__histograms[tablekey] = None        
        
        self.__rates = {ratekey:self.__getrate(tables[ratekey] if ratekey in tables.keys() else kwargs[ratekey], date, *args, basis=basis, **kwargs) for ratekey in self.__ratetables}
        self.__counts = {countkey:self.__getcount(tables[countkey], date, *args, **kwargs) for countkey in self.__counttables}
        self.__concepts = {conceptkey:Concept(self.__histograms, *args, **kwargs) for conceptkey, Concept in concepts.items()}
            
    def __getitem__(self, key):
        if key in self.__counts: return self.__counts[key]
        elif key in self.__rates: return self.__rates[key]
        elif key in self.__concepts: return self.__concepts[key]
        elif key in self.__histograms: return self.__histograms[key]
        else: raise KeyError(key)

    def __getcount(self, table, date, *args, **kwargs): return table.sel(**{'date':date}).squeeze('date').arrays[table.datakeys[0]][()]    
    def __gethistogram(self, table, date, *args, **kwargs): return table.sel(**{'date':date}).squeeze('date').tohistogram(*args, how='average', **kwargs)
    
    @typedispatcher
    def __getrate(self, table, date, *args, extrapolate, basis, weights=None, **kwargs): 
        try: table = table.tocurve(*args, how='average', **kwargs)           
        except AttributeError: raise TypeError(type(table))
        return Rate(table.xvalues, table.yvalues, w=weights, extrapolate=extrapolate, basis=basis)
    
    @__getrate.register(int, float, Number)
    def __getrateNumber(self, rate, date, *args, extrapolate, basis, **kwargs):
        return Rate(date.index, rate, extrapolate=extrapolate, basis=basis)     


class MonteCarlo(object):
    @property
    def keys(self): return list(self.__histograms.keys())
    @property
    def histograms(self): return list(self.__histograms.values())
    @property
    def variables(self): return {histogram.axiskey:histogram.axisvariable for histogram in self.__histograms.values()}

    def __init__(self, **histograms):
        self.__histograms = ODict([(key, value) for key, value in histograms.items()])
        self.__correlationmatrix = np.zeros((len(histograms), len(histograms)))
        np.fill_diagonal(self.__correlationmatrix, 1)
        
    def samplematrix(self, size, *args, method='cholesky', **kwargs):
        try: size = int(size)
        except: size = size.astype('int64')
        samplematrix = np.array([histogram(size) for histogram in self.__histograms.values()]) 
        if method == 'cholesky':
            correlation_matrix = cholesky(self.__correlationmatrix, lower=True)
        elif method == 'eigen':
            evals, evecs = eigh(self.__correlationmatrix)
            correlation_matrix = np.dot(evecs, np.diag(np.sqrt(evals)))
        else: raise ValueError(method)
        return np.dot(correlation_matrix, samplematrix) 
    
    def sampledataframe(self, size, *args, **kwargs):
        try: size = int(size)
        except: size = size.astype('int64')
        samplematrix = self.samplematrix(size, *args, **kwargs)    
        sampletable = {key:list(values) for key, values in zip(self.keys, samplematrix)}
        return pd.DataFrame(sampletable)        
    
    def __call__(self, size, *args, **kwargs):
        for index, values in self.sampledataframe(size).iterrows():  
            values = {key:self.variables[key].fromindex(value) for key, value in values.to_dict().items()}
            yield index, values  

    