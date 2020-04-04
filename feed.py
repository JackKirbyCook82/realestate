# -*- coding: utf-8 -*-
"""
Created on Tues Mar 31 2020
@name:   Real Estate Feed Objects
@author: Jack Kirby Cook

"""

import numpy as np
from scipy.interpolate import interp1d

from tables.transformations import Reduction
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
summation = Reduction(how='summation', by='summation')


class ValueFeed(dict):
    def __init__(self, *args, **kwargs):
        for key, tableID in self.tableIDs.items():
            print(renderer(calculations[tableID]))
            self[key] = calculations[tableID](*args, **kwargs)
            assert self[key].layers == 1        

    def __execute(self, table, *args, **kwargs):
        assert table.dim == 1
        x = np.array([table.variables[self.axis].fromstr(string).value for string in table.headers[self.axis]])
        y = table.arrays[table.datakeys[0]]
        assert len(x) == len(y)
        return x, y
        
    def __call__(self, *args, **kwargs): 
        for key, table in self.items(): yield key, self.__execute(table, *args, **kwargs)   
           
    @classmethod
    def create(cls, name, axis, **tableIDs):
        def wrapper(subclass): return type(subclass.__name__, (subclass, cls), {'name':name, 'axis':axis, 'tableIDs':tableIDs})
        return wrapper


class HistogramFeed(dict):
    def __init__(self, *args, geography, date, dates=None, **kwargs):
        for key, tableID in self.tableIDs.items():
            print(renderer(calculations[tableID]))
            self[key] = calculations[tableID](*args, geography=geography, date=date, **kwargs)
            assert self[key].layers == 1
        
    def __execute(self, table, *args, geography=None, **kwargs):
        if geography is not None: table = table[{'geography':geography}].squeeze('geography')
        else: table = summation(table, *args, axis='geography', **kwargs).squeeze('geography')         
        assert table.dim == 1
        return table.tohistogram()        
        
    def __call__(self, *args, **kwargs): 
        for key, table in self.items(): yield key, self.__execute(table, *args, **kwargs)   
           
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

@ValueFeed.create('rate', 'date', **RATE_TABLES)
class RateFeed: pass









