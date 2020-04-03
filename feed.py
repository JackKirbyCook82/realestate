# -*- coding: utf-8 -*-
"""
Created on Tues Mar 31 2020
@name:   Real Estate Feed Objects
@author: Jack Kirby Cook

"""

import numpy as np
from scipy.interpolate import interp1d

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from uscensus.calculations import process, renderer

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['FinanceFeed', 'HouseholdFeed', 'HousingFeed', 'RateFeed']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item is not None]
_yearrate =  {'year': lambda rate: float(rate), 'month': lambda rate: float(pow(rate + 1, 12) - 1)} 
_monthrate = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_normalize = lambda items: np.array(items) / np.sum(np.array(items))
_curve = lambda x, y, z: interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[np.argmin(x)], z)) 

RATE_TABLES = {'income':'Δ%avginc', 'value':'Δ%avgval@owner', 'rent':'Δ%avgrent@renter'}
HOUSING_TABLES = {'yearoccupied':'#st|geo|yrblt', 'rooms':'#st|geo|rm', 'bedrooms':'#st|geo|br', 'commute':'#pop|geo|cmte'}
FINANCE_TABLES = {'income':'#hh|geo|~inc', 'value':'#hh|geo|~val', 'rent':'#hh|geo|~rent'}
HOUSEHOLD_TABLES = {'age':'#hh|geo|~age', 'yearoccupied':'#st|geo|~yrocc', 'size':'#hh|geo|~size', 'children':'#hh|geo|child', 
                    'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'race':'#pop|geo|race', 'origin':'#pop|geo|origin'}
                 
calculations = process()


class HistogramFeed(dict):
    def __init__(self, *args, **kwargs):
        for key, tableID in self.tableIDs.items():
            print(renderer(calculations[tableID]))
            self[key] = calculations[tableID](*args, **kwargs)
            assert self[key].layers == 1
        
    def __call__(self, *args, **kwargs): 
        for key, table in self.items():        
            table = self.__squeeze(table, *args, axis='geography', **kwargs)
            table = self.__squeeze(table, *args, axis='date', **kwargs)
            assert len(table.headers['geography']) == len(table.headers['date']) == 1
            yield key, table.tohistogram()

    def curve(self, key, *args, method='average', **kwargs): 
        table = self[key]
        for axis in table.axes: 
            if axis in kwargs.keys(): table = self.__squeeze(table, *args, axis=axis, **kwargs)
            else: pass
        x = np.array([table.variables[key].fromstr(string).value for string in table.headers[key]])
        y = table.arrays[table.datakeys[0]]
        return self.__createcurve(method, x, y, *args, **kwargs)

    @keydispatcher
    def __createcurve(self, method, x, y, *args, **kwargs): raise KeyError(method)
    @__createcurve.register('average')
    def __average(self, x, y, *args, weights=None, **kwargs): return _curve(x, y, np.average(y, weights=_normalize(weights) if weights else None))
    @__createcurve.register('last')
    def __last(self, x, y, *args, **kwargs): return _curve(x, y, y[np.argmax(y)])
            
    def __squeeze(self, table, *args, axis, **kwargs):
        axisargument = kwargs.get(axis, None)
        if hasattr(axisargument, '__call__'): return axisargument(table, *args, axis=axis, **kwargs).squeeze(axis)
        elif isinstance(axisargument, str): return table[{axis, axisargument}].squeeze(axis)
        elif axisargument is None: return table.squeeze(axis)        
        else: raise ValueError(axisargument)    
   
    @classmethod
    def create(cls, name, **tableIDs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'name':name, 'tableIDs':tableIDs})
        return wrapper
            
    
@HistogramFeed.create('finance', **FINANCE_TABLES)
class FinanceFeed: pass

@HistogramFeed.create('household', **HOUSEHOLD_TABLES)
class HouseholdFeed: pass

@HistogramFeed.create('housing', **HOUSING_TABLES)
class HousingFeed: pass

@HistogramFeed.create('rate', **RATE_TABLES)
class RateFeed: pass
















