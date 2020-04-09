# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Economy Objects
@author: Jack Kirby Cook

"""

import numpy as np
from scipy.interpolate import interp1d
from scipy.linalg import cholesky, eigh
from itertools import chain
from collections import namedtuple as ntuple

from utilities.strings import uppercase
from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Broker', 'Loan', 'School', 'Bank']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_yearrate =  {'year': lambda rate: float(rate), 'month': lambda rate: float(pow(rate + 1, 12) - 1)} 
_yearduration = {'year': lambda duration: int(duration), 'month': lambda duration: int(duration * 12)}
_monthrate = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}
_normalize = lambda items: np.array(items) / np.sum(np.array(items))
_curve = lambda x, y, z: interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[np.argmin(x)], z)) 

_payment = lambda x, r, n: x * (r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
_balance = lambda x, r, n: x * (pow(1 + r, n) - pow(1 + r, n)) / (pow(1 + r, n) - 1)  
_downpayment = lambda x, ltv: x * (1 - ltv)
_financingcost = lambda x, r: x * (1 + r)


@keydispatcher
def curve(method, x, y, *args, **kwargs): raise KeyError(method)
@curve.register('average')
def average(x, y, w, *args, **kwargs): return _curve(x, y, np.average(y, weights=_normalize(w) if w else None))
@curve.register('last')
def last(x, y, *args, **kwargs): return _curve(x, y, y[np.argmax(x)])   
        
        
class Loan(ntuple('Loan', 'type balance rate duration')):
    stringformat = 'Loan|{type} ${balance} for {duration}MO @{rate}%/MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  
    def __hash__(self): return hash((self.__class__.__name__, self.type, self.balance, self.rate, self.duration,))       
    
    def __new__(cls, *args, rate, duration, basis='month', **kwargs): 
        return super().__new__(cls, *args, _monthrate[basis](rate), _monthduration[basis](duration), **kwargs)   
    
    @property
    def payment(self): return _payment(self.balance, self.rate, self.duration)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    def projection(self, duration): return self.__class__(self.type, _balance(self.balance, self.rate, self.duration), self.rate, max(self.duration - duration, 0))
    def payoff(self): return self.projection(self.duration)
    
    
class Broker(ntuple('Broker', 'commisions')): 
    stringformat = 'Broker|{commisions}%' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))          
    def cost(self, amount): return amount * (1 + self.commisions)    
 
    
class School(ntuple('Education', 'type cost duration')):
    stringformat = 'School|{type} costing ${cost} over {duration}MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  
    
    def __new__(cls, *args, duration, basis='year', **kwargs): 
        return super().__new__(cls, *args, duration=_monthduration[basis](duration), **kwargs) 

    
class Bank(ntuple('bank', 'type rate duration financing coverage loantovalue')):
    stringformat = 'Bank|{type} providing {rate}%/MO for {duration}MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))      
    
    def __new__(cls, *args, rate, duration, financing=0, coverage=0, loantovalue=1, basis='year', **kwargs): 
        return super().__new__(cls, *args, rate=_monthrate[basis](rate), duration=_monthduration[basis](duration), financing=financing, coverage=coverage, loantovalue=loantovalue, **kwargs)  

    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)
    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return _downpayment(value, self.loantovalue)
    def cost(self, amount): return _financingcost(amount, self.financing)


#class Environment(object):
#    def __init__(self, geography, date, *args, rates, banks, education, broker, finance, households, housing, **kwargs):
#        self.__geography, self.__date = geography, date
#        assert isinstance(broker, Broker)
#        assert all([isinstance(school, School) for school in education.values()])
#        assert all([isinstance(bank, Bank) for bank in banks.values()])
#        for histogram in chain(finance.values(), households.values(), housing.values()): 
#            assert histogram.scope['geography'] == str(geography) 
#            assert histogram.scope['date'] == str(date)
#        self.__finance, self.__households, self.__housing = finance, households, housing
#        self.__rates = rates


#class MonteCarlo(object):
#    __instances = {}
#    def __new__(cls, *args, geography, date, **kwargs):
#        key = hash((cls.__name__, hash(date), hash(geography),))
#        instance = cls.__instances.get(key, super().__new__(cls))
#        if key not in cls.__instances.keys(): cls.__instances[key] = instance
#        return instance
#
#    def __init__(self, tables, *args, **kwargs):
#        self.__tables = {key:gettable(tableID, *args, **kwargs) for key, tableID in self.tableIDs.items()}
#        self.__correlationmatrix = np.zero((len(self), len(self)))
#        np.fill_diagonal(self.__correlationmatrix, 1)
#        
#    def __call__(self, size, *args, **kwargs):
#        if 'geography' in kwargs.keys(): tables = {key:table[{'geography':kwargs['geography']}] for key, table in self.__tables.items()}
#        else: tables = {key:self.summation(table, *args, axis='geography', weights=self.__weights, **kwargs) for key, table in self.__tables.items()}
#        tables = {key:table.tohistorgram() for key, table in tables.items()}
#        concepts = ODict([(table.axiskey, table.concepts) for table in tables.values()])
#        keys = [table.axiskey for table in tables.values()]
#        samplematrix = self.__samplematrix(tables, size, *args, **kwargs)                      
#        
#    def __samplematirx(self, tables, size, *args, method='cholesky', **kwargs):
#        samplematrix = np.array([table(size) for table in tables.values()]) 
#        if method == 'cholesky':
#            correlation_matrix = cholesky(self.__correlationmatrix, lower=True)
#        elif method == 'eigen':
#            evals, evecs = eigh(self.__correlationmatrix)
#            correlation_matrix = np.dot(evecs, np.diag(np.sqrt(evals)))
#        else: raise ValueError(method)
#        return np.dot(correlation_matrix, samplematrix).transpose()    
    
    
    
    
    
    
    
    
    
    
    
    