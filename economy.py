# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Economy Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Broker', 'Loan', 'School', 'Bank']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_yearrate =  {'year': lambda rate: float(rate), 'month': lambda rate: float(pow(rate + 1, 12) - 1)} 
_yearduration = {'year': lambda duration: int(duration), 'month': lambda duration: int(duration * 12)}
_monthrate = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}

_payment = lambda x, r, n: x * (r * pow(1 + r, n)) / (pow(1 + r, n) - 1)
_balance = lambda x, r, n: x * (pow(1 + r, n) - pow(1 + r, n)) / (pow(1 + r, n) - 1)  
_downpayment = lambda x, ltv: x * (1 - ltv)
_financingcost = lambda x, r: x * (1 + r)


class Loan(ntuple('Loan', 'type balance rate duration')):
    stringformat = '{name}|${balance} for {duration}-MOS @{rate}%/MO' 
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
    
    
class Broker(ntuple('Broker', 'name commisions')): 
    stringformat = '{name}|Broker charging {commisions}%' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))          
    def cost(self, amount): return amount * (1 + self.commisions)    
 
    
class School(ntuple('Education', 'type name cost duration')):
    stringformat = '{name}|{type}School costing ${cost} over {duration}-YRS' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  
    
    def __new__(cls, *args, duration, basis='year', **kwargs): 
        return super().__new__(cls, *args, duration=_yearduration[basis](kwargs['duration']), **kwargs) 

    
class Bank(ntuple('bank', 'type name rate duration financing coverage loantovalue')):
    stringformat = '{name}|{type}Bank providing {rate}%/MO for {duration}-MOS' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})          
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))      
    
    def __new__(cls, *args, rate, duration, financing=0, coverage=0, loantovalue=1, basis='year', **kwargs): 
        return super().__new__(cls, *args, rates=_monthrate[basis](kwargs['rates']), duration=_monthduration[basis](kwargs['duration']), financing=financing, coverage=coverage, loantovalue=loantovalue, **kwargs)  

    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)
    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return _downpayment(value, self.loantovalue)
    def cost(self, amount): return _financingcost(amount, self.financing)



    
    