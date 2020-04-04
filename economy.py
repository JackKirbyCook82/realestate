# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Economy Objects
@author: Jack Kirby Cook

"""

import numpy as np
from scipy.interpolate import interp1d
from collections import namedtuple as ntuple

from utilities.strings import uppercase
from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Broker', 'Rate', 'Loan', 'School', 'Bank']
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


class Rate(ntuple('Rate', 'type date curve')):
    stringformat = 'Rate|{type} {rate}%/MO @{date}'
    def __str__(self): return self.stringformat.format(**{'type':uppercase(self.type), 'rate':curve(self.date), 'date':self.date})    
    def __call__(self, x): return self.curve(x)
        
    def __new__(cls, name, x, y, *args, method='average', basis='year', **kwargs): 
        w = kwargs.get('weights', np.ones(len(y)))
        x, y, w, t = np.array(x), np.vectorize(lambda i: _monthrate[basis](i))(y), _normalize(w), np.argmax(x)
        assert len(x) == len(y) == len(w)
        return super().__new__(cls, name, t, curve(method, x, y, w, *args, **kwargs))


class Loan(ntuple('Loan', 'type balance rate duration')):
    stringformat = 'Loan|{type} ${balance} for {duration}-MOS @{rate}%/MO' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
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
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))          
    def cost(self, amount): return amount * (1 + self.commisions)    
 
    
class School(ntuple('Education', 'type name cost duration')):
    stringformat = 'School|{type} costing ${cost} over {duration}-YRS' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  
    
    def __new__(cls, *args, duration, basis='year', **kwargs): 
        return super().__new__(cls, *args, duration=_monthduration[basis](kwargs['duration']), **kwargs) 

    
class Bank(ntuple('bank', 'type rate duration financing coverage loantovalue')):
    stringformat = 'Bank|{type} providing {rate}%/MO for {duration}-MOS' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))      
    
    def __new__(cls, *args, rate, duration, financing=0, coverage=0, loantovalue=1, basis='year', **kwargs): 
        return super().__new__(cls, *args, rates=_monthrate[basis](kwargs['rates']), duration=_monthduration[basis](kwargs['duration']), financing=financing, coverage=coverage, loantovalue=loantovalue, **kwargs)  

    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)
    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return _downpayment(value, self.loantovalue)
    def cost(self, amount): return _financingcost(amount, self.financing)



    
    