# -*- coding: utf-8 -*-
"""
Created on Tues Mar 31 2020
@name:   Real Estate Feed Objects
@author: Jack Kirby Cook

"""

import numpy as np

from tables.transformations import Reduction
from uscensus.calculations import process, renderer

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Rate_History', 'Households_MonteCarlo', 'Housing_MonteCarlo']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item is not None]

WEIGHT_TABLES = {'income':'#hh|geo', 'value':'#hh|geo@owner', 'rent':'#hh|geo@renter'}
RATE_TABLES = {'income':'Δ%avginc|geo', 'value':'Δ%avgval|geo@owner', 'rent':'Δ%avgrent|geo@rent'}
HOUSING_TABLES = {}
FINANCE_TABLES = {'income':'#hh|geo|~inc', 'value':'#hh|geo|~val', 'rent':'#hh|geo|~rent'}
HOUSEHOLD_TABLES = {'age':'#hh|geo|~age', 'yearoccupied':'#st|geo|~yrocc', 'size':'#hh|geo|~size', 'children':'#hh|geo|child', 
                    'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'race':'#pop|geo|race', 'origin':'#pop|geo|origin'}
                 
calculations = process()
summation = Reduction(how='summation', by='summation') 
average = Reduction(how='wtaverage', by='summation')

rendertable = lambda tableID:  print(renderer(calculations[tableID]))
gettable = lambda tableID, *args, **kwargs: calculations[tableID](*args, **kwargs)   
getyears = lambda table: np.array([int(i) for i in table.headers['date']])
getrates = lambda table: table.arrays[table.datakeys[0]]


class Rate_History(object):
    def __str__(self): return '\n'.join([str(table) for table in self.__tables])
    def __init__(self, *args, **kwargs):
        self.__tables = {key:gettable(tableID, *args, **kwargs) for key, tableID in RATE_TABLES.items()}
        self.__weights = {key:gettable(tableID, *args, **kwargs).arrays[key] for key, tableID in WEIGHT_TABLES.items()}
    
    def __call__(self, *args, **kwargs):
        if 'geography' in kwargs.keys(): tables = {key:table[{'geography':kwargs['geography']}] for key, table in self.__tables.items()}
        else: tables = {key:self.average(table, *args, axis='geography', weights=self.__weights, **kwargs) for key, table in self.__tables.items()}
        return {key:(getyears(table), getrates(table)) for key, table in tables.items()}


class MonteCarlo(object):
    __instances = {}
    def __new__(cls, *args, geography, date, **kwargs):
        key = hash((cls.__name__, hash(date), hash(geography),))
        instance = cls.__instances.get(key, super().__new__(cls))
        if key not in cls.__instances.keys(): cls.__instances[key] = instance
        return instance

    def __init__(self, tables, *args, **kwargs):
        self.__tables = {key:gettable(tableID, *args, **kwargs) for key, tableID in self.tableIDs.items()}
        
    def create(cls, **tableIDs):
        def wrapper(subclass): return type(subclass.__name__, (cls, subclass), {'tableIDs':tableIDs})
        return wrapper


@MonteCarlo.create(**FINANCE_TABLES, **HOUSEHOLD_TABLES)
class Households_MonteCarlo(MonteCarlo): pass

@MonteCarlo.create(**HOUSING_TABLES)
class Housing_MonteCarlo(MonteCarlo): pass





















