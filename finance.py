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
__all__ = ['Economy', 'Broker', 'MortgageBank', 'CreditBank', 'StudentLoanBank', 'Loan', 'Financials', 'InsufficientFundsError', 'InsufficientCoverageError', 'UnstableLifeStyleError']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_monthrate= {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}
_monthincome = {'year': lambda income: int(income / 12), 'month': lambda income: int(income)}


def theta(*args, risktolerance, discountrate, wealthrate, **kwargs): 
    return (wealthrate - discountrate) / risktolerance   

def income_integral(horizon, *args, incomerate, wealthrate, **kwargs): 
    r = incomerate - wealthrate
    return (pow(1 + r, horizon) - 1) / r

def consumption_integal(horizon, *args, wealthrate, **kwargs): 
    r = theta(wealthrate=wealthrate, **kwargs) - wealthrate
    return  (pow(1 + r, horizon) - 1) / r

def loan_integral(horizon, *args, loanrate, wealthrate, **kwargs):     
    l = loanrate  / (pow(1 + loanrate, horizon) - 1)    
    w = wealthrate / (pow(1 + wealthrate, horizon) - 1)
    return  l * pow(1 + loanrate, horizon) / w

def wealth_integral(horizon, wealthmultiple, *args, wealthrate, **kwargs):
    return 1 - (wealthmultiple / pow(1 + wealthrate, horizon)) 

def income_compounding(horizon, *args, incomerate, wealthrate, **kwargs):
    return np.array([pow(1 + incomerate, i) * pow(1 + wealthrate, i) for i in range(1, horizon+1, 1)])

def consumption_compounding(horizon, *args, discountrate, risktolerance, wealthrate, **kwargs):
    return np.array([pow(1 + theta(risktolerance, discountrate, wealthrate), i) * pow(1 + wealthrate, i) for i in range(1, horizon+1, 1)])    


def bank(banktype, *fields):
    def __new__(cls, basis, *args, name, rate, duration, **kwargs): 
        return super(cls, cls).__new__(cls, *args, name=name, rate=_monthrate[basis](rate), duration=_monthduration[basis](duration), **kwargs)          
    def __call__(self, amount): 
        return Loan('month', banktype, amount, self.rate, self.duration)

    stringformat = '{name}|Providing {rate}%/MO for {duration}-MOS' 
    def __str__(self): return self.stringformat.format()        
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))  

    def decorator(subclass): 
        base = ntuple(subclass.__name__, ' '.join(['name', 'rate', 'duration', *fields]))
        attrs = {'__new__':__new__, '__call__':__call__, '__str__':__str__, '__repr__':__repr__, stringformat:stringformat}
        return type(subclass.__name__, (subclass, base), attrs)
    return decorator

@bank('mortgage', 'financing', 'coverage', 'loantovalue')
class MortgageBank: pass
@bank('credit')
class CreditBank: pass
@bank('studentloan')
class StudentLoanBank: pass
    

class Broker(ntuple('Broker', 'commisions')): pass
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
    def __new__(cls, basis, *args, name, balance, rate, duration, **kwargs): return super().__new__(cls, name, balance, _monthrate[basis](rate), _monthduration[basis](duration))   
    
    @property
    def payment(self): return (self.balance * self.rate * pow(1 + self.rate, self.duration))/(pow(1 + self.rate, self.duration) - 1)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    def step(self, *args, **kwargs): 
        return self.__class__(self.name, min(self.balance - self.principal, 0), self.rate, self.duration - 1)
    def projection(self, duration, *args, **kwargs): 
        duration = min(duration, self.duration)
        newbalance = self.balance * (pow(self.factor, duration) - pow(self.factor, self.duration)) / (pow(self.factor, duration) - 1)
        return self.__class__(self.name, min(newbalance, 0), self.rate, self.duration - duration)


class InsufficientFundsError(Exception): pass
class InsufficientCoverageError(Exception): pass
class UnstableLifeStyleError(Exception): pass
class ExceededHorizonError(Exception): pass


class Financials(ntuple('Financials', 'discountrate risktolerance income wealth value mortgage studentloan debt')):
    stringformat = 'Financials|Assets=${assets:.0f}, Debt=${debt:.0f}, Income=${income:.0f}/MO'
    def __str__(self): return self.stringformat(assets=self.wealth+self.value, income=self.income, debt=self.mortgage.balance + self.studentloan.balance + self.debt.balance)   
    
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, repr(self[field])]) for field in self._fields]))  
    def __hash__(self): return hash((self.__class__.__name__, self.discountrate, self.risktolerance, self.wealth, self.income, hash(self.mortgage), hash(self.studentloan), hash(self.debt),))    
    
    def __new__(cls, basis, *args, discountrate, risktolerance, wealth, income, value, mortgage=None, studentloan=None, debt=None, **kwargs):        
        if mortgage is None: mortgage = Loan('mortgage', 0, 0, 0) 
        if studentloan is None: studentloan = Loan('studentloan', 0, 0, 0)
        if debt is None: debt = Loan('debt', 0, 0, 0)
        assert all([isinstance(loan, Loan) for loan in (mortgage, studentloan, debt)])
        return super().__new__(cls, _monthrate[basis](discountrate), risktolerance, wealth, _monthincome[basis](income), value, mortgage, studentloan, debt)     
    
    def __init__(self, horizon, incomehorizon, wealthmultiple, *args, economy, concepts, **kwargs): 
        i = income_integral(min(incomehorizon, horizon), **economy.rates) 
        c = consumption_integal(horizon, **economy.rates, **self.rates)    
        w = wealth_integral(horizon, wealthmultiple, **economy.rates)
        m = loan_integral(min(horizon, self.mortgage.duration), loanrate=self.mortgage.rate, **economy.rates)  
        s = loan_integral(min(horizon, self.studentloan.duration), loanrate=self.studentloan.rate, **economy.rates)  
        d = loan_integral(min(horizon, self.debt.duration), loanrate=self.debt.rate, **economy.rates) 
        consumption = (w * self.wealth + i * self.income - m * self.mortgage.balance - s * self.studentloan.balance - d * self.debt.balance) / c
        if consumption < 0: raise UnstableLifeStyleError()        
        self.__horizon, self.__incomehorizon = horizon, incomehorizon
        self.__consumption = consumption
        self.__concepts = concepts
    
    @property
    def rates(self): return dict(discountrate=self.discountrate, risktolerance=self.risktolerance)
    @property
    def loans(self): return dict(mortgage=self.mortgage, studentloan=self.studentloan, debt=self.debt)
    @property
    def assets(self): return dict(income=self.income, wealth=self.wealth, value=self.value)
    
    @property
    def consumption(self): return self.__consumption
    @property    
    def savings(self): return self.income - self.__consumption  
    
    @property
    def coverage(self): return self.income / (self.mortgage.payment + self.studentloan.payment + self.debt.payment)
    @property
    def loantovalue(self): return self.mortgage / self.value

    def __proceeds(self, commisions): return self.value * (1 - commisions) - self.mortgage.balance 
    def __commisions(self, value, commisions): return value * (1 + commisions)
    def __financing(self, value, financing): return value * (1 + financing)
    def __downpayment(self, value, loantovalue): return value * (1 - loantovalue)
    
    def sale(self, *args, broker, **kwargs): return self.__class__(self.wealth + self.__proceeds(broker.commisions), self.income, 0, None, self.studentloan, self.debt)
    def buy(self, value, *args, broker, mortgagebank, **kwargs): 
        closingcost = self.__commisions(value, broker.commisions, mortgagebank.financing)
        downpayment = self.__downpayment(value, mortgagebank.loantovalue)
        mortgage = mortgagebank(value - downpayment)
        newfinancials = self.__class__(self.discountrate, self.risktolerance, self.wealth - downpayment - closingcost, self.income, value, mortgage, self.studentloan, self.debt)
        if newfinancials.wealth < 0: raise InsufficientFundsError()  
        if newfinancials.coverage < bank.coverage: raise InsufficientCoverageError()
        return newfinancials

    def step(self, *args, economy, **kwargs):
        if self.__horizon < 1: raise ExceededHorizonError()
        newwealth = self.wealth * (1 + economy.wealthrate) + self.savings
        newincome = self.income * (1 + economy.incomerate)
        newvalue = self.value * (1 + economy.valuerate)
        newmortgage = self.mortgage.step(*args, **kwargs) 
        newstudentloan = self.studentloan.step(*args, **kwargs)
        newdebt = self.debt.step(*args, **kwargs)
        rates = dict(discountrate=self.discountrate, risktolerance=self.risktolerance)
        loans = dict(mortgage=newmortgage, studentloan=newstudentloan, debt=newdebt)
        assets = dict(income=newincome, wealth=newwealth, value=newvalue)
        return self.__class__(self.__horizon-1, self.__incomehorizon-1, economy=economy, concepts=self.__concepts, **assets, **rates, **loans)           

    def projection(self, duration, *args, economy, **kwargs):  
        if self.__horizon < duration: raise ExceededHorizonError()
        income = income_compounding(min(duration, self.__incomehorizon), **economy.rates, **self.rates)
        consumption = consumption_compounding(duration, **economy.rates, **self.rates)        
        savings = income - consumption
        newwealth = self.wealth * pow(1 + economy.wealthrate, duration) + savings
        newincome = self.income * pow(1 + economy.incomerate, duration)
        newvalue = self.value * pow(1 + economy.valuerate, duration)
        newmortgage = self.mortgage.projection(duration, *args, **kwargs) 
        newstudentloan = self.studentloan.projection(duration, *args, **kwargs)
        newdebt = self.debt.projection(duration, *args, **kwargs)
        rates = dict(discountrate=self.discountrate, risktolerance=self.risktolerance)
        loans = dict(mortgage=newmortgage, studentloan=newstudentloan, debt=newdebt)
        assets = dict(income=newincome, wealth=newwealth, value=newvalue)
        return self.__class__(self.__horizon-duration, max(0, self.__incomehorizon-duration), economy=economy, concepts=self.__concepts, **assets, **rates, **loans)           














