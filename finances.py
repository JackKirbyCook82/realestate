# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Finances
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple
from numbers import Number

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Rates', 'Durations', 'Economy', 'Loan', 'Financials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class Rates(ntuple('Rates', 'discount wealth value income mortgage studentloan debt')):     
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, self[field]]) for field in self._fields]))        
    def __new__(cls, basis, *args, **kwargs): 
        if basis == 'year': function = lambda rate: pow(rate + 1, 1/12) - 1
        elif basis == 'month': function = lambda rate: rate
        else: raise ValueError(basis)
        return super().__new__(cls, *[float(function(rate)) for rate in cls._fields])
        
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()        
    
    def theta(self, risk): return (self.wealth - self.discount) / risk    
    def income_integral(self, horizon): return (1 - pow(1 + self.income - self.wealth, horizon)) / (self.income - self.wealth)
    def consumption_integal(self, horizon, risk): return (1 - pow(1 + self.theta(risk) - self.wealth, horizon)) / (self.theta(risk) - self.wealth)
    
    def mortgage_integral(self, horizon): return self.loan_integral(self, 'mortgage', horizon) 
    def studentloan_integral(self, horizon): return self.loan_integral(self, 'studentloan', horizon) 
    def debt_integal(self, horizon): return self.loan_integral(self, 'debt', horizon) 
    
    def loan_integral(self, loan, horizon): return self.__loanfactor(loan) * (pow(1 - self.wealth, horizon) - 1) / self.wealth
    def __loanfactor(self, loan, horizon): return (getattr(self, loan) * pow(1 + getattr(self, loan), horizon)) / (pow(1 + getattr(self, loan), horizon) - 1)


class Durations(ntuple('Duration', 'mortgage studentloan debt')):
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, self[field]]) for field in self._fields]))          
    def __new__(cls, basis, *args, **kwargs): 
        if basis == 'year': function = lambda rate: rate * 12
        elif basis == 'month': function = lambda rate: rate
        else: raise ValueError(basis)        
        return super().__new__(cls, *[int(function(rate)) for rate in cls._fields])    
    
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    
    

class Economy(ntuple('Economy', 'rates durations risk price commisions financing coverage loantovalue')):
    def __repr__(self): 
        function = lambda field: self[field] if isinstance(field, Number) else repr(self[field])
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, function(field)]) for field in self._fields]))       
    
    def __new__(cls, *args, rates, durations, **kwargs):
        assert isinstance(rates, Rates)
        assert isinstance(rates, Durations)
        return super().__new__(cls, rates, durations, *[field for field in cls._fields])    
    
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    
    

class Loan(ntuple('Loan', 'name balance rate duration')):
    stringformat = '{name}|${balance} for {duration}PERS @{rate}%/PER' 
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, self[field]]) for field in self._fields]))  
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
          
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    

    @property
    def factor(self): return 1 + self.rate
    @property
    def payment(self): return (self.balance * self.rate * pow(self.factor, self.duration))/(pow(self.factor, self.duration) - 1)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    def __call__(self, duration): 
        duration = min(duration, self.duration)
        newbalance = self.balance * (pow(self.factor, duration) - pow(self.factor, self.duration)) / (pow(self.factor, duration) - 1)
        return self.__class__(min(newbalance, 0), self.rate, self.duration - duration)


class InsufficientFundsError(Exception):
    def __init__(self, financials): super().__init__('available={}, required={}'.format(financials.wealth, 0))

class InsufficientCoverageError(Exception):
    def __init__(self, financials, coverage): super().__init__('available={}, required={}'.format(financials.coverage, coverage))

class UnstableLifeStyleError(Exception):
    def __init__(self, consumption): super().__init__('available={}, required={}'.format(consumption, 0))


class Financials(ntuple('Financials', 'wealth income value mortgage studentloan debt')):
    def __new__(cls, *args, wealth, income, value, mortgage, studentloan, debt, **kwargs):        
        if mortgage is None: mortgage = Loan('mortgage', 0, 0, 0) 
        if studentloan is None: studentloan = Loan('studentloan', 0, 0, 0)
        if debt is None: debt = Loan('debt', 0, 0, 0)
        assert all([isinstance(loan, Loan) for loan in (mortgage, studentloan, debt)])
        return super().__new__(cls, wealth, income, value, mortgage, studentloan, debt)   
    
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()
    
    @property
    def coverage(self): return self.income / (self.mortgage.payment + self.studentloan.payment + self.debt.payment)
    @property
    def loantovalue(self): return self.mortgage / self.value

    def __proceeds(self, commisions): return self.value * (1 - commisions) - self.mortgage.balance 
    def __commisions(self, value, commisions): return value * (1 + commisions)
    def __financing(self, value, financing): return value * (1 + financing)
    def __downpayment(self, value, loantovalue): return value * (1 - loantovalue)
    
    def sale(self, *args, economy, **kwargs): return self.__class__(self.wealth + self.__proceeds(economy.commisions), self.income, 0, None, self.studentloan, self.debt)
    def buy(self, value, *args, economy, **kwargs): 
        closingcost = self.__commisions(value, economy.commisions, economy.financing)
        downpayment = self.__downpayment(value, economy.loantovalue)
        mortgage = Loan('mortgage', value - downpayment, economy.rates.mortgage, economy.durations.mortgage)
        newfinancials = self.__class__(self.wealth - downpayment - closingcost, self.income, value, mortgage, self.studentloan, self.debt)
        if newfinancials.wealth < 0: raise InsufficientFundsError(newfinancials)  
        if newfinancials.coverage < economy.coverage: raise InsufficientCoverageError(newfinancials, economy.coverage)
        return newfinancials
          
    def __call__(self, household, *args, economy, **kwargs): 
        w = self.wealth - (household.horizonwealth / pow(1 + economy.rates.wealth, household.horizon)) 
        i = economy.rates.income_integral(min(household.horizon, household.retirement))
        c = economy.rates.consumption_integal(household.horizon, economy.risk)
        m = economy.rates.mortgage_integral(min(household.horizon, self.mortgage.duration))
        s = economy.rates.studentloan_integral(min(household.horizon, self.studentloan.duration))
        d = economy.rates.debt_integal(min(household.horizon, self.debt.duration))        
        consumption = (w + (i * self.income) - (m * self.mortgage.balance) - (s * self.studentloan.balance) - (d * self.debt.balance)) / c
        if consumption < 0: raise UnstableLifeStyleError(consumption)
        return consumption
       





