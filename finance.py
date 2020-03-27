# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
from collections import namedtuple as ntuple

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Economy', 'Loan', 'Financials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_monthrate= {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}
_monthincome = {'year': lambda income: int(income / 12), 'month': lambda income: int(income)}

_loanfactor = lambda horizon, loanrate: loanrate  / (pow(1 + loanrate, horizon) - 1)   
_wealthfactor = lambda horizon, wealthrate: wealthrate / (pow(1 + wealthrate, horizon) - 1)

def theta(*args, risktolerance, discountrate, wealthrate, **kwargs): 
    return (wealthrate - discountrate) / risktolerance   

def income_compounding(horizon, *args, incomerate, wealthrate, **kwargs): 
    return np.array([pow(1 + incomerate, i) * pow(1 + wealthrate, i) for i in range(1, horizon+1, 1)])
def consumption_compounding(horizon, *args, discountrate, risktolerance, wealthrate, **kwargs): 
    return np.array([pow(1 + theta(risktolerance, discountrate, wealthrate), i) * pow(1 + wealthrate, i) for i in range(1, horizon+1, 1)])    

def income_integral(horizon, *args, incomerate, wealthrate, **kwargs): 
    return (pow(1 + incomerate - wealthrate, horizon) - 1) / (incomerate - wealthrate)
def consumption_integal(horizon, *args, wealthrate, **kwargs): 
    return  (pow(1 +theta(wealthrate=wealthrate, **kwargs) - wealthrate, horizon) - 1) / (theta(wealthrate=wealthrate, **kwargs) - wealthrate)
def loan_integral(horizon, *args, loanrate, wealthrate, **kwargs): 
    return _loanfactor(horizon, loanrate) * pow(1 + loanrate, horizon) / _wealthfactor(horizon, wealthrate)


class Economy(ntuple('Econcomy', 'wealthrate incomerate valuerate price')): 
    @property
    def rates(self): return dict(wealthrate=self.wealthrate, incomerate=self.incomerate, valuerate=self.valuerate)
    def __new__(cls, basis, *args, wealthrate, incomerate, valuerate, price, **kwargs):      
        return super().__new__(cls, _monthrate[basis](wealthrate), _monthrate[basis](incomerate), _monthrate[basis](valuerate), price)


class Loan(ntuple('Loan', 'name balance rate duration')):
    stringformat = '{name}|${balance} for {duration}-MOS @{rate}%/MO' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  
    def __hash__(self): return hash((self.__class__.__name__, self.name, self.balance, self.rate, self.duration,))       
    def __new__(cls, *args, name, balance, rate, duration, basis='month', **kwargs): return super().__new__(cls, name, balance, _monthrate[basis](rate), _monthduration[basis](duration))   
    
    @property
    def payment(self): return (self.balance * self.rate * pow(1 + self.rate, self.duration))/(pow(1 + self.rate, self.duration) - 1)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    
class InsufficientFundsError(Exception): pass
class InsufficientCoverageError(Exception): pass
class UnstableLifeStyleError(Exception): pass
class ExceededHorizonError(Exception): pass


class Financials(ntuple('Financials', 'discountrate risktolerance income wealth value consumption mortgage studentloan debt')):
    stringformat = 'Financials|Assets=${assets:.0f}, Debt=${debt:.0f}, Income=${income:.0f}/MO'
    def __str__(self): return self.stringformat(assets=self.wealth + self.value, income=self.income, debt=self.mortgage.balance + self.studentloan.balance + self.debt.balance)   
    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, repr(self[field])]) for field in self._fields]))  
    def __hash__(self): return hash((self.__class__.__name__, self.discountrate, self.risktolerance, self.wealth, self.income, hash(self.mortgage), hash(self.studentloan), hash(self.debt),))    

    def __new__(cls, *args, basis='month', **kwargs):        
        kwargs.update({kwargs.get(loan, Loan(loan, 0, 0, 0)) for loan in ('mortgage', 'studentloan', 'debt')})
        assert all([isinstance(kwargs.get(loan), Loan) for loan in ('mortgage', 'studentloan', 'debt')])
        kwargs.update({'discountrate':_monthrate(kwargs['discountrate']), 'income':_monthincome(kwargs['income'])})
        consumption = cls.__consumption(*args, **kwargs)       
        return super().__new__(cls, consumption=consumption, **kwargs)     

    @classmethod
    def __consumption(cls, horizon, incomehorizon, *args, wealth, targetwealth, income, mortgage, studentloan, debt, economy, **kwargs):
        w = wealth - targetwealth / pow(1 + economy.wealthrate, horizon)        
        i = income_integral(min(incomehorizon, horizon), **economy.rates) 
        c = consumption_integal(horizon, **economy.rates, **kwargs)    
        m = loan_integral(min(horizon, mortgage.duration), loanrate=mortgage.rate, **economy.rates)  
        s = loan_integral(min(horizon, studentloan.duration), loanrate=studentloan.rate, **economy.rates)  
        d = loan_integral(min(horizon, debt.duration), loanrate=debt.rate, **economy.rates) 
        consumption = (w + i * income - m * mortgage.balance - s * studentloan.balance - d * debt.balance) / c        
        if consumption < 0: raise UnstableLifeStyleError()   
        else: return consumption    
     
    def __init__(self, horizon, incomehorizon, *args, **kwargs):
        self.__horizon, self.__incomehorizon = horizon, incomehorizon
        
    @property
    def rates(self): return dict(discountrate=self.discountrate, risktolerance=self.risktolerance)
    @property
    def loans(self): return dict(mortgage=self.mortgage, studentloan=self.studentloan, debt=self.debt)
    @property
    def assets(self): return dict(income=self.income, wealth=self.wealth, value=self.value)
    
    @property
    def coverage(self): return self.income / (self.mortgage.payment + self.studentloan.payment + self.debt.payment)
    @property
    def loantovalue(self): return self.mortgage / self.value

    def sale(self, *args, broker, **kwargs): 
        proceeds = self.value - broker.cost(self.value) - self.mortgage.balance 
        return self.__class__(self.wealth + proceeds, self.income, 0, None, self.studentloan, self.debt)
    
    def buy(self, value, *args, bank, **kwargs): 
        downpayment = bank.downpayment(value)
        closingcost = bank.cost(value - downpayment)
        mortgage = bank.loan(value - downpayment)
        newfinancials = self.__class__(self.discountrate, self.risktolerance, self.wealth - downpayment - closingcost, self.income, value, mortgage, self.studentloan, self.debt)
        if newfinancials.wealth < 0: raise InsufficientFundsError()  
        if not bank.qualify(newfinancials.coverage): raise InsufficientCoverageError()
        return newfinancials

    def terminal(self, *args, **kwargs): return self.projection(self.__horizon, *args, **kwargs)
    def projection(self, duration, *args, economy, **kwargs):  
        if self.__horizon < duration: raise ExceededHorizonError()
        income = self.income * income_compounding(min(duration, self.__incomehorizon), **economy.rates, **self.rates)
        consumption = self.consumption * consumption_compounding(duration, **economy.rates, **self.rates)        
        newwealth = self.wealth * pow(1 + economy.wealthrate, duration) + income - consumption
        newincome = self.income * pow(1 + economy.incomerate, duration)
        newvalue = self.value * pow(1 + economy.valuerate, duration)
        newmortgage = self.mortgage.projection(duration, *args, **kwargs) 
        newstudentloan = self.studentloan.projection(duration, *args, **kwargs)
        newdebt = self.debt.projection(duration, *args, **kwargs)
        rates = dict(discountrate=self.discountrate, risktolerance=self.risktolerance)
        loans = dict(mortgage=newmortgage, studentloan=newstudentloan, debt=newdebt)
        assets = dict(income=newincome, wealth=newwealth, value=newvalue)
        return self.__class__(self.__horizon - duration, max(0, self.__incomehorizon - duration), economy=economy, **assets, **rates, **loans)  







