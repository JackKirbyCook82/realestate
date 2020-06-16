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
__all__ = ['Economy', 'Rate', 'Broker', 'Loan', 'Education', 'Bank']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_convertKeys = ['year', 'month', 'week']
_convertMatrix = np.array([[1, 12, 52], [1/12, 1, 52/12], [1/52, 12/52, 1]]) 
_convertindex = lambda key: _convertKeys.index(key)
_convertfactor = lambda fromvalue, tovalue: _convertMatrix[_convertindex(fromvalue), _convertindex(tovalue)]
_convertrate = lambda frombasis, tobasis, rate: pow((1 + rate), pow(_convertfactor(frombasis, tobasis), -1)) - 1
_convertduration = lambda frombasis, tobasis, duration: duration * _convertfactor(frombasis, tobasis)

_aslist = lambda items: [items] if isinstance(items, Number) else items
_normalize = lambda items: np.array(items) / np.sum(np.array(items))
_curve = lambda x, y, fill: interp1d(x, y, kind='linear', bounds_error=False, fill_value=fill) 

downpayment = lambda x, ltv: x * (1 - ltv)
financingcost = lambda x, r: x * r
loantovalue = lambda x, v: x / v   
loanvalue = lambda x, r, n, i: np.fv(r, i, -np.pmt(r, n, x), -x)


@keydispatcher
def createcurve(method, x, y, *args, **kwargs): raise KeyError(method)
@createcurve.register('average')
def createcurve_average(x, y, *args, **kwargs): return _curve(x, y, (np.average(y), np.average(y)))
@createcurve.register('last')
def createcurve_last(x, y, *args, **kwargs): return _curve(x, y, (y[np.argmin(x)], y[np.argmax(x)]))   


class Economy(ntuple('Economy', 'wealthrate incomerate inflationrate date purchasingpower')):
    def __repr__(self):    
        content = {'purchasingpower':self.purchasingpower}
        content.update({field:repr(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))
    

class Rate(ntuple('Rate', 'x y basis')):
    def __new__(cls, x, y, *args, basis, **kwargs):
        if isinstance(x, np.ndarray) and isinstance(y, np.ndarray): assert x.shape == y.shape
        else:
            try: x, y = np.array([x]), np.array([y]) 
            except: raise TypeError(type(x), type(y))
        return super().__new__(cls, x, y, basis)
   
    def __call__(self, x, *args, units, **kwargs): return float(_convertrate(self.basis, units, self.__curve(x)))
    def __repr__(self): return '{}(x={}, y={}, basis={})'.format(self.__class__.__name__, self.x, self.y, self.basis)
    def __init__(self, *args, extrapolate='average', **kwargs): 
        if len(self.x) > 1: self.__curve = createcurve(extrapolate, self.x, self.y, *args, **kwargs)
        else: self.__curve = lambda x: self.y
            
    
class Loan(ntuple('Loan', 'type balance rate duration')):
    stringformat = 'Loan|{type} of ${balance:.0f} @ {rate:.3f}%/YR for {duration:.0f}MOS' 
    emptystringformat = 'Loan|{type} of ${balance:.0f}'
    def __str__(self): 
        content = {'type':uppercase(self.type), 'balance':self.balance, 'rate':_convertrate('month', 'year', self.rate), 'duration':self.duration}
        return self.stringformat.format(**content) if self else self.emptystringformat.format(**content)
    
    def __repr__(self):
        content = {'type':self.type, 'balance':round(self.balance, ndigits=1), 'rate':round(self.rate, ndigits=4), 'duration':self.duration}
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, str(value)]) for key, value in content.items()])) 
   
    @property
    def key(self): return (self.type, int(self.balance), round(self.rate, 3), int(self.duration),)
    def __ne__(self, other): return not self.__eq__()
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return self.key == other.key
    
    def __bool__(self): return self.balance > 0    
    def __new__(cls, loantype, *args, balance, rate=None, duration=0, basis, **kwargs): 
        rate = _convertrate(basis, 'month', rate) if balance > 0 else 0
        duration = max(int(_convertduration(basis, 'month', duration)), 0)
        balance = balance if balance else 0
        return super().__new__(cls, loantype, balance, rate, duration)    

    @property
    def payment(self): return -np.pmt(self.rate, self.duration, self.balance) if self.balance else 0
    def projection(self, horizon):
        balance = loanvalue(self.balance, self.rate, self.duration, min(horizon, self.duration)) if self.balance else 0
        duration = max(self.duration - horizon, 0)
        return self.__class__(self.type, balance=balance, duration=duration, rate=self.rate, basis='month')


class Broker(ntuple('Broker', 'commissions')): 
    stringformat = 'Broker|{commissions:.3f}%' 
    def __str__(self): return self.stringformat.format(commissions=self.commissions)          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    def cost(self, amount): return amount * (1 + self.commisions)    
 
    
class Education(ntuple('Education', 'type cost duration')):
    stringformat = 'Education|{type} costing ${cost:.0f} over {duration:.0f}MOS' 
    def __str__(self): 
        content = {'type':uppercase(self.type), 'cost':self.cost, 'duration':self.duration}
        return self.stringformat.format(**content)          
    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    def __new__(cls, *args, duration, basis, **kwargs): 
        duration = max(int(_convertduration(basis, 'month', duration)), 0)
        return super().__new__(cls, *args, duration=duration, **kwargs) 

    
class Bank(ntuple('Bank', 'type rate duration financing coverage loantovalue')):
    stringformat = 'Bank|{type} providing {rate:.3f}%/YR loans for {duration:.0f}MOS' 
    def __str__(self): 
        content = {'type':uppercase(self.type), 'rate':_convertrate('month', 'year', self.rate), 'duration':self.duration, 'financing':self.financing, 'coverage':self.coverage, 'loantovalue':self.loantovalue}
        return self.stringformat.format(**content)          
    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, dictstring(self._asdict()))
    def __new__(cls, *args, rate, duration, financing=0, coverage=0, loantovalue=1, basis, **kwargs): 
        rate = _convertrate(basis, 'month', rate)
        duration = max(int(_convertduration(basis, 'month', duration)), 0)
        return super().__new__(cls, *args, rate=rate, duration=duration, financing=financing, coverage=coverage, loantovalue=loantovalue, **kwargs)  

    def loan(self, amount): return Loan(self.type, balance=amount, rate=self.rate, duration=self.duration, basis='month')
    def downpayment(self, value): return downpayment(value, self.loantovalue)
    def cost(self, amount): return financingcost(amount, self.financing)


    
    
    
    
    
    
    
    