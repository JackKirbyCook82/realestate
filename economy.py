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
__all__ = ['Economy', 'Loan', 'CreditBank', 'StudentLoanBank', 'MortgageBank']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_yearrate =  {'year': lambda rate: float(rate), 'month': lambda rate: float(pow(rate + 1, 12) - 1)} 
_monthrate = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}
_normalize = lambda items: np.array(items) / np.sum(np.array(items))
_curve = lambda x, y, z: interp1d(x, y, kind='linear', bounds_error=False, fill_value=(y[np.argmin(x)], z)) 


class Economy(object): 
    @keydispatcher
    def __createcurve(self, method, years, values, *args, **kwargs): raise KeyError(method)
    @__createcurve.register('average')
    def __average(self, years, values, *args, weights=None, **kwargs): return _curve(years, values, np.average(values, weights=_normalize(weights) if weights else None))
    @__createcurve.register('last')
    def __last(self, years, values, *args, **kwargs): return _curve(years, values, values[np.argmax(values)])
    
    def __init__(self, years, *args, wealthrates, incomerates, valuerates, basis='year', method='average', **kwargs):        
        yearfunction = np.vectorize(lambda x: int(x))
        ratefunction = np.vectorize(lambda x: _yearrate[basis](x))
        self.__wealthcurve = self.__createcurve(method, yearfunction(years), ratefunction(wealthrates), *args, **kwargs)
        self.__incomecurve = self.__createcurve(method, yearfunction(years), ratefunction(incomerates), *args, **kwargs)
        self.__valuecurve = self.__createcurve(method, yearfunction(years), ratefunction(valuerates), *args, **kwargs)
        
    def wealthrate(self, year, *args, basis='month', **kwargs): return _monthrate[basis](self.__wealthcurve(year))
    def incomerate(self, year, *args, basis='month', **kwargs): return _monthrate[basis](self.__incomecurve(year))
    def valuerate(self, year, *args, basis='month', **kwargs): return _monthrate[basis](self.__valuecurve(year))
    def rates(self, year, *args, **kwargs): return self.wealthrate(year, *args, **kwargs), self.incomerate(year, *args, **kwargs), self.valuerate(year, *args, **kwargs)    


class Loan(ntuple('Loan', 'name balance rate duration')):
    stringformat = '{name}|${balance} for {duration}-MOS @{rate}%/MO' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  
    def __hash__(self): return hash((self.__class__.__name__, self.name, self.balance, self.rate, self.duration,))       
    def __new__(cls, *args, name, balance, rate, duration, basis='month', **kwargs): return super().__new__(cls, name, balance, _monthrate[basis](rate), _monthduration[basis](duration))   
    
#    @property
#    def payment(self): return (self.balance * self.rate * pow(1 + self.rate, self.duration))/(pow(1 + self.rate, self.duration) - 1)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    def payoff(self): return self.projection(self.duration)
#    def projection(self, duration): 
#        balance = self.balance * (pow(1 + self.rate, self.duration) - pow(1 + self.rate, min(duration, self.duration))) / (pow(1 + self.rate, self.duration) - 1)
#        return self.__class__(self.name, balance, self.rate, max(self.duration - duration, 0))
  
    
class Broker(ntuple('Broker', 'commisions')): 
    def cost(self, amount): return amount * (1 + self.commisions)    
    
    
class Bank(ntuple('bank', 'type name rate duration')):
    stringformat = '{name}|{type}Bank providing {rate}%/MO for {duration}-MOS' 
    def __str__(self): return self.stringformat.format(**{'type':uppercase(self.type)}, name=self.name, rate=self.rate, duration=self.duration)        
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))      
    def __new__(cls, *args, basis='month', rate, duration, **kwargs): 
        kwargs.update({'rates':_monthrate[basis](kwargs['rates']), 'duration':_monthduration[basis](kwargs['duration'])})
        return super().__new__(cls, **kwargs)                      
    
    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)

    
class CreditBank(Bank): 
    def __new__(cls, *args, **kwargs): return super().__new__(cls, *args, **{'type':'credit'}, **kwargs)
    
class StudentLoanBank(Bank): 
    def __new__(cls, *args, **kwargs): return super().__new__(cls, *args, **{'type':'studentloan'}, **kwargs)
     
class MortgageBank(Bank): 
    def __new__(cls, *args, **kwargs): return super().__new__(cls, *args, **{'type':'mortgage'}, **kwargs)
    def __init__(self, *args, financing, coverage, loantovalue, **kwargs): self.financing, self.coverage, self.loantovalue = financing, coverage, loantovalue

    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return value * (1 - self.loantovalue)
    def cost(self, amount): return amount * (1 + self.financing)



    
    