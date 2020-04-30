# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 2020
@name:   Real Estate Constructor Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.linalg import cholesky, eigh
from collections import OrderedDict as ODict
from collections import namedtuple as ntuple

from utilities.strings import uppercase
from utilities.concepts import concept
from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['environment']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]
_normalize = lambda items: np.array(items) / np.sum(np.array(items))
_curve = lambda x, y, z: interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[np.argmin(x)], z)) 


@keydispatcher
def curve(method, x, y, *args, **kwargs): raise KeyError(method)
@curve.register('average')
def average(x, y, *args, weights=None, **kwargs): return _curve(x, y, np.average(y, weights=_normalize(weights) if weights else None))
@curve.register('last')
def last(x, y, *args, **kwargs): return _curve(x, y, y[np.argmax(x)])   


class FeedNotCalculatedError(Exception): pass
class FeedAlreadyCalculatedError(Exception): pass


class Feed(object):
    @property
    def calculated(self): return self.__calculated

    def __init__(self, calculations, renderer, **tables): 
        self.__calculations = calculations
        self.__renderer = renderer
        self.__queue = tables
        self.__tables = {}
        self.__calculated = False    
        
    def calculate(self, *args, geography, dates, **kwargs):
        if self.calculated: raise FeedNotCalculatedError()        
        for tableKey, tableID in self.__queue.items():
            print(self.__renderer(self.__calculations[tableID]), '\n')
            self.__tables[tableKey] = self.__calculations[tableID](*args, geography=geography, dates=_aslist(dates), **kwargs)
        self.__calculated = True        

    def __iter__(self):
        if not self.calculated: raise FeedAlreadyCalculatedError()
        for table in self.__tables.values(): yield table

#    def __call__(self, *args, geography, date=None, **kwargs):
#        if not self.calculated: raise FeedNotCalculatedError()
#        tables = {tableKey:table.sel(geography=geography).squeeze('geography') for tableKey, table in self.__tables.items()}
#        if date: tables = {tableKey:table.sel(date=date).squeeze('date') for tableKey, table in tables.items()}    
#        return {tableKey:table.tohistogram() for tableKey, table in tables.items()}


class Environment(ntuple('Environment', 'histograms curves')):
    @property
    def geography(self): return self.__geography
    @property
    def date(self): return self.__date    
    
    def __init__(self, *args, geography, date, **kwargs):                
        self.__geography = geography
        self.__date = date
        
    def sample(self, key): return MonteCarlo(**self.histograms[key])    
    def curves(self, key, *args, method, **kwargs): return {curve(method, curvetable.xvalues, curvetable.yvalues, *args, **kwargs) for curvetable in self.curves[key].values()}
    def concept(self, key): 
        if key in self.histograms.keys(): return concept(key, fields=list(self.histograms[key].keys()))(**self.histograms[key])
        elif key in self.curves.keys(): return concept(key, fields=list(self.curves[key].keys()))(**self.curves[key])
        else: raise KeyError(key)    
        
    
def environment(name, *args, histograms, curves, **kwargs):
    def __new__(cls, *args, **kwargs):
        function = lambda fields: {field:kwargs.get(field, None) for field in fields}
        return super().__new__(cls, function(cls.histogram_fields), function(cls.curve_fields), function(cls.sample_fields))
    
    name = ''.join([uppercase(name), Environment.__name__])
    bases = (Environment,)
    attrs = {'__new__':__new__, 'histogram_fields':histograms, 'curve_fields':curves}
    return type(name, bases, attrs)


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








    