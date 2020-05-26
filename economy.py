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
from utilities.strings import uppercase, dictstring

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

payment = lambda x, r, n: x * (r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
balance = lambda x, r, n: x * (pow(1 + r, n) - pow(1 + r, n)) / (pow(1 + r, n) - 1)  
downpayment = lambda x, ltv: x * (1 - ltv)
financingcost = lambda x, r: x * (1 + r)


@keydispatcher
def createcurve(method, x, y, *args, **kwargs): raise KeyError(method)
@createcurve.register('average')
def createcurve_average(x, y, *args, weights=None, **kwargs): return _curve(x, y, np.average(y, weights=_normalize(weights) if weights else None))
@createcurve.register('last')
def createcurve_last(x, y, *args, **kwargs): return _curve(x, y, y[np.argmax(x)])   


class Economy(ntuple('Economy', 'geography date ages rates schools banks broker')):
    def __new__(cls, geography, date, *args, ages, rates, schools, banks, broker, **kwargs):
        rates = {key:(Rate.fromcurve(value, *args, **kwargs) if hasattr(value, '__call__') else Rate.frompoint(date.year, value, *args, **kwargs)) for key, value in rates.items()}
        return super().__new__(cls, geography, date, ages, rates, schools, banks, broker)


class Rate(object): 
    def __repr__(self): return '{}(curve={}, basis={})'.format(self.__class__.__name__, repr(self.__curve), self.__basis)
    def __init__(self, curve, *args, basis='year', **kwargs): self.__curve, self.__basis = curve, basis
    def __call__(self, date, *args, basis='month', **kwargs): return _convertrate(self.__basis, basis, self.__curve(date)[()])
    
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
    stringformat = 'Loan|{type} ${balance:.0f} for {duration:.0f}MO @{rate:.2f}%/MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
#    def __hash__(self): raise Exception('HASH TABLE REQUIRED')
    
    def __new__(cls, *args, rate, duration, basis='month', **kwargs): 
        return super().__new__(cls, *args, _convertrate(basis, 'month', rate), _convertduration(basis, 'month', duration), **kwargs)    
    
    @property
    def payment(self): return payment(self.balance, self.rate, self.duration)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    def projection(self, duration): return self.__class__(self.type, balance(self.balance, self.rate, self.duration), self.rate, max(self.duration - duration, 0))
    def payoff(self): return self.projection(self.duration)
    
    
class Broker(ntuple('Broker', 'commisions')): 
    stringformat = 'Broker|{commisions:.2f}%' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    def cost(self, amount): return amount * (1 + self.commisions)    
 
    
class School(ntuple('Education', 'type cost duration')):
    stringformat = 'School|{type} costing ${cost:.0f} over {duration:.0f} MOS' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    
    def __new__(cls, *args, duration, basis='year', **kwargs): 
        return super().__new__(cls, *args, duration=_convertduration(basis, 'month', duration), **kwargs) 

    
class Bank(ntuple('Bank', 'type rate duration financing coverage loantovalue')):
    stringformat = 'Bank|{type} providing {rate:.2f}%/MO loans for {duration:.0f} MOS' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    
    def __new__(cls, *args, rate, duration, financing=0, coverage=0, loantovalue=1, basis='year', **kwargs): 
        rate, duration = _convertrate(basis, 'month', rate), _convertduration(basis, 'month', duration)
        return super().__new__(cls, *args, rate=rate, duration=duration, financing=financing, coverage=coverage, loantovalue=loantovalue, **kwargs)  

    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)
    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return downpayment(value, self.loantovalue)
    def cost(self, amount): return financingcost(amount, self.financing)



    
    
    
    