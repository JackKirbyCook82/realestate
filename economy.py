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
__all__ = ['Rate', 'Broker', 'Loan', 'Education', 'Bank']
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
def createcurve_average(x, y, *args, **kwargs): return _curve(x, y, np.average(y, weights=None))
@createcurve.register('last')
def createcurve_last(x, y, *args, **kwargs): return _curve(x, y, y[np.argmax(x)])   


class Rate(ntuple('Rate', 'x y basis')):
    def __new__(cls, x, y, *args, basis, **kwargs):
        if isinstance(x, np.ndarray) and isinstance(y, np.ndarray): assert x.shape == y.shape
        else:
            try: x, y = np.array([x, x]), np.array([y, y]) 
            except: raise TypeError(type(x), type(y))
        return super().__new__(cls, x, y, basis)
    
    def __repr__(self): return '{}(x={}, y={}, basis={})'.format(self.__class__.__name__, self.__x, self.__y, self.__basis)
    def __init__(self, *args, extrapolate='average', **kwargs): self.__curve = createcurve(extrapolate, self.x, self.y, *args, **kwargs)
    def __call__(self, x, *args, basis, **kwargs): return _convertrate(self.basis, basis, self.__curve(x)[()])
            
    
class Loan(ntuple('Loan', 'type balance rate duration')):
    stringformat = 'Loan|{type} ${balance:.0f} for {duration:.0f}MO @{rate:.2f}%/MO' 
    def __str__(self): return self.stringformat.format(**{key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    
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
 
    
class Education(ntuple('Education', 'type cost duration')):
    stringformat = 'Education|{type} costing ${cost:.0f} over {duration:.0f} MOS' 
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



    
    
    
    