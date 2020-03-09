# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Finance
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Economy', 'Broker', 'MortgageBank', 'CreditBank', 'StudentLoanBank', 'Loan', 'Financials', 'InsufficientFundsError', 'InsufficientCoverageError', 'UnstableLifeStyleError']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


def theta(risktolerance, discountrate, wealthrate): 
    return (wealthrate - discountrate) / risktolerance   
def income_integral(horizon, incomerate, wealthrate): 
    x = 1 - pow(1 + incomerate - wealthrate, horizon) 
    y = incomerate - wealthrate  
    return x / y
def consumption_integal(horizon, discountrate, wealthrate, risktolerance): 
    x = 1 - pow(1 + theta(risktolerance, discountrate, wealthrate) - wealthrate, horizon)
    y = theta(risktolerance, discountrate, wealthrate) - wealthrate
    return  x / y
def loan_integral(horizon, loanrate, wealthrate): 
    x = (loanrate * pow(1 + loanrate, horizon)) / (pow(1 + loanrate, horizon) - 1)
    y = (pow(1 - wealthrate, horizon) - 1) / wealthrate 
    return  x * y 


def bank(name, *fields):
    def __new__(cls, basis, *args, rate, duration, **kwargs):
        durationfunctions = {'year': lambda rate: int(rate * 12), 'month': lambda rate: int(rate)}
        ratefunctions = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)}          
        return super().__new__(cls, *args, rate=ratefunctions[basis](rate), duration=durationfunctions[basis](duration), **kwargs)
          
    base = ntuple(name, ' '.join(['rate', 'duration', *fields]))
    attrs = {'__new__':__new__}
    
    def decorator(subclass): return type(name, (subclass, base), attrs)
    return decorator

@bank('financing', 'coverage', 'loantovalue')
class MortgageBank: pass
@bank.create()
class CreditBank: pass
@bank.create()
class StudentLoanBank: pass
    

class Broker(ntuple('Broker', 'commisions')): pass

class Economy(ntuple('Econcomy', 'wealthrate incomerate price')): 
    def __new__(cls, basis, *args, wealthrate, incomerate, price, **kwargs):
        ratefunctions = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)}          
        return super().__new__(cls, wealthrate=ratefunctions[basis](wealthrate), incomerate=ratefunctions[basis](incomerate), price=price)


class Loan(ntuple('Loan', 'name balance rate duration')):
    stringformat = '{name}|${balance} for {duration}PERS @{rate}%/PER' 
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})    
          
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


class Financials(ntuple('Financials', 'discountrate risktolerance wealth income value mortgage studentloan debt')):
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, repr(self[field])]) for field in self._fields]))  
    def __new__(cls, basis, *args, discountrate, risktolerance, wealth, income, value, mortgage, studentloan, debt, **kwargs):        
        ratefunctions = {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)}  
        if mortgage is None: mortgage = Loan('mortgage', 0, 0, 0) 
        if studentloan is None: studentloan = Loan('studentloan', 0, 0, 0)
        if debt is None: debt = Loan('debt', 0, 0, 0)
        assert all([isinstance(loan, Loan) for loan in (mortgage, studentloan, debt)])
        return super().__new__(cls, ratefunctions[basis](discountrate), risktolerance, wealth, income, value, mortgage, studentloan, debt)   
    
    @property
    def coverage(self): return self.income / (self.mortgage.payment + self.studentloan.payment + self.debt.payment)
    @property
    def loantovalue(self): return self.mortgage / self.value

    def __proceeds(self, commisions): return self.value * (1 - commisions) - self.mortgage.balance 
    def __commisions(self, value, commisions): return value * (1 + commisions)
    def __financing(self, value, financing): return value * (1 + financing)
    def __downpayment(self, value, loantovalue): return value * (1 - loantovalue)
    
    def sale(self, *args, broker, **kwargs): return self.__class__(self.wealth + self.__proceeds(broker.commisions), self.income, 0, None, self.studentloan, self.debt)
    def buy(self, value, *args, broker, bank, **kwargs): 
        closingcost = self.__commisions(value, broker.commisions, bank.financing)
        downpayment = self.__downpayment(value, bank.loantovalue)
        mortgage = Loan('mortgage', value - downpayment, bank.rates, bank.durations)
        newfinancials = self.__class__(self.discountrate, self.risktolerance, self.wealth - downpayment - closingcost, self.income, value, mortgage, self.studentloan, self.debt)
        if newfinancials.wealth < 0: raise InsufficientFundsError(newfinancials)  
        if newfinancials.coverage < bank.coverage: raise InsufficientCoverageError(newfinancials, bank.coverage)
        return newfinancials
      
    def __call__(self, household, *args, economy, **kwargs): 
        w = self.wealth - (household.horizonwealth / pow(1 + economy.wealthrate, household.horizon)) 
        i = income_integral(min(household.horizon, household.retirement), economy.incomerate, economy.wealthrate)
        c = consumption_integal(household.horizon, self.discountrate, economy.wealthrate, self.risktolerance)
        m = loan_integral(min(household.horizon, self.mortgage.duration), self.mortgage.rate, economy.wealthrate)
        s = loan_integral(min(household.horizon, self.studentloan.duration), self.studentloan.rate, economy.wealthrate)
        d = loan_integral(min(household.horizon, self.debt.duration), self.debt.rate, economy.wealthrate)        
        consumption = (w + (i * self.income) - (m * self.mortgage.balance) - (s * self.studentloan.balance) - (d * self.debt.balance)) / c
        if consumption < 0: raise UnstableLifeStyleError(consumption)
        return consumption
       














