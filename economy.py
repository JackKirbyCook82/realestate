# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Economy Objects
@author: Jack Kirby Cook

"""

import numpy as np
from scipy.interpolate import interp1d
from numbers import Number
from collections import namedtuple as ntuple

from utilities.dispatchers import key_singledispatcher as keydispatcher
from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Rate', 'Broker', 'Loan', 'School', 'Bank']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_convertKeys = ['year', 'month', 'week']
_convertMatrix = np.array([[1, 12, 52], [-12, 1, 52/12], [-52, -52/12, 1]]) 
_convertindex = lambda key: _convertKeys.index(key)
_convertfactor = lambda fromvalue, tovalue: _convertMatrix[_convertindex(fromvalue), _convertindex(tovalue)]
_convertrate = lambda frombasis, tobasis, rate: pow((1 + rate), _convertfactor(frombasis, tobasis)) - 1
_convertduration = lambda frombasis, tobasis, duration: duration * _convertfactor(frombasis, tobasis)

_aslist = lambda items: [items] if isinstance(items, Number) else items
_normalize = lambda items: np.array(items) / np.sum(np.array(items))
_curve = lambda x, y, z: interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[np.argmin(x)], z)) 

_payment = lambda x, r, n: x * (r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
_balance = lambda x, r, n: x * (pow(1 + r, n) - pow(1 + r, n)) / (pow(1 + r, n) - 1)  
_downpayment = lambda x, ltv: x * (1 - ltv)
_financingcost = lambda x, r: x * (1 + r)


@keydispatcher
def createcurve(method, x, y, *args, **kwargs): raise KeyError(method)
@createcurve.register('average')
def createcurve_average(x, y, *args, weights=None, **kwargs): return _curve(x, y, np.average(y, weights=_normalize(weights) if weights else None))
@createcurve.register('last')
def createcurve_last(x, y, *args, **kwargs): return _curve(x, y, y[np.argmax(x)])   


class Economy(ntuple('Economy', 'geography date rates schools banks broker')):
    def __new__(cls, geography, date, *args, rates, schools, banks, broker, **kwargs):
        rates = {key:(Rate.fromcurve(value, *args, **kwargs) if hasattr(value, '__call__') else Rate.frompoint(date.year, value, *args, **kwargs)) for key, value in rates.items()}
        return super().__new__(cls, geography, date, rates, schools, banks, broker)


class Rate(object): 
    def __init__(self, curve, *args, basis='year', **kwargs): 
        self.__curve = curve
        self.__basis = basis
    
    def __call__(self, date, *args, basis='month', **kwargs): 
        rate = self.__curve(date)
        factor = _convertrate(self.__basis, basis, date)
        return pow((1 + rate), factor) - 1
    
    @classmethod
    def fromcurve(cls, curve, *args, **kwargs): return cls(curve, *args, **kwargs)     
    @classmethod
    def fromvalues(cls, x, y, *args, method='average', **kwargs): 
        curve = createcurve(method, x, y, *args, **kwargs)
        return cls(curve, *args, **kwargs)
    @classmethod
    def frompoint(cls, x, y, *args, **kwargs): 
        curve = createcurve('last', [x, x], [y, y], *args, **kwargs)
        return cls(curve, *args, **kwargs)
            
    
class Loan(ntuple('Loan', 'type balance rate duration')):
    stringformat = 'Loan|{type} ${balance} for {duration}MO @{rate}%/MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, repr(value)]) for key, value in self._asdict().items()])) 
    def __hash__(self): return hash((self.__class__.__name__, self.type, self.balance, self.rate, self.duration,))       
    
    def __new__(cls, *args, rate, duration, basis='month', **kwargs): 
        return super().__new__(cls, *args, _convertrate(basis, 'month', rate), _convertduration(basis, 'month', duration), **kwargs)    
    
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
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, repr(value)]) for key, value in self._asdict().items()]))         
    def cost(self, amount): return amount * (1 + self.commisions)    
 
    
class School(ntuple('Education', 'type cost duration')):
    stringformat = 'School|{type} costing ${cost} over {duration}MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, repr(value)]) for key, value in self._asdict().items()])) 
    
    def __new__(cls, *args, duration, basis='year', **kwargs): 
        return super().__new__(cls, *args, duration=_convertduration(basis, 'month', duration), **kwargs) 

    
class Bank(ntuple('Bank', 'type rate duration financing coverage loantovalue')):
    stringformat = 'Bank|{type} providing {rate}%/MO for {duration}MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, repr(value)]) for key, value in self._asdict().items()])) 
    
    def __new__(cls, *args, rate, duration, financing=0, coverage=0, loantovalue=1, basis='year', **kwargs): 
        rate, duration = _convertrate(basis, 'month', rate), _convertduration(basis, 'month', duration)
        return super().__new__(cls, *args, rate=rate, duration=duration, financing=financing, coverage=coverage, loantovalue=loantovalue, **kwargs)  

    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)
    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return _downpayment(value, self.loantovalue)
    def cost(self, amount): return _financingcost(amount, self.financing)



    
    
    
    