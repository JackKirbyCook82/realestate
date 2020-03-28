# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Financials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_monthrate= {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}
_monthflow = {'year': lambda flow: int(flow / 12), 'month': lambda flow: int(flow)}

def theta(risktolerance, discountrate, wealthrate): return (wealthrate - discountrate) / risktolerance   
#def income_compounding(duration, incomerate, wealthrate): return np.array([pow(1 + incomerate, i) * pow(1 + wealthrate, i) for i in range(1, duration + 1, 1)])
#def consumption_compounding(duration, discountrate, risktolerance, wealthrate): return np.array([pow(1 + theta(risktolerance, discountrate, wealthrate), i) * pow(1 + wealthrate, i) for i in range(1, duration + 1, 1)])    
#def income_integral(duration, incomerate, wealthrate): pass 
#def consumption_integral(duration, discountrate, risktolerance, wealthrate): pass
#def loanpayment_integral(duration, loanrate, wealthrate): pass


class InsufficientFundsError(Exception): pass
class InsufficientCoverageError(Exception): pass
class UnstableLifeStyleError(Exception): pass
class ExceededHorizonError(Exception): pass


class Financials(ntuple('Financials', 'discountrate risktolerance income wealth value consumption mortgage studentloan debt')):
    stringformat = 'Financials|Assets=${assets:.0f}, Debt=${debt:.0f}, Income=${income:.0f}/MO'
    def __str__(self): return self.stringformat(assets=self.wealth + self.value, income=self.income, debt=self.mortgage.balance + self.studentloan.balance + self.debt.balance)     
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, repr(self[field])]) for field in self._fields]))  
    def __hash__(self): return hash((self.__class__.__name__, self.discountrate, self.risktolerance, self.income, self.wealth, self.value, self.consumption, hash(self.mortgage), hash(self.studentloan), hash(self.debt),))    

    def __new__(cls, *args, basis='month', **kwargs):        
        kwargs.update({'discountrate':_monthrate(kwargs['discountrate']), 'income':_monthflow(kwargs['income'])})
        consumption = cls.__consumption(*args, **kwargs)       
        return super().__new__(cls, consumption=consumption, **kwargs)     

    @classmethod
    def __consumption(cls, lifeduration, incomeduration, *args, discountrate, risktolerance, income, wealth, value, mortgage, studentloan, debt, wealthrate, incomerate, valuerate, basis='month', **kwargs):
        wealthrate, incomerate, valuerate = [_monthrate[basis](rate) for rate in (wealthrate, incomerate, valuerate)]
#       
        i = income_integral(min(lifeduration, incomeduration), incomerate, wealthrate) 
        c = consumption_integral(lifeduration, discountrate, risktolerance, wealthrate)    
        m = loanpayment_integral(min(lifeduration, mortgage.duration), mortgage.rate, wealthrate)  
        s = loanpayment_integral(min(lifeduration, studentloan.duration), studentloan.rate, wealthrate)  
        d = loanpayment_integral(min(lifeduration, debt.duration), debt.rate, wealthrate)         
#             
        if consumption < 0: raise UnstableLifeStyleError()   
        else: return int(consumption)    
             
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
        loans = dict(mortgage=self.mortgage.payoff(), studentloan=self.studentloan, debt=self.debt)
        assets = dict(income=self.income, wealth=self.wealth + proceeds, value=0)
        newfinancials = self.__class__(**assets, **self.rates, **loans)  
        return newfinancials
    
    def buy(self, value, *args, bank, **kwargs): 
        downpayment = bank.downpayment(value)
        closingcost = bank.cost(value - downpayment)
        mortgage = bank.loan(value - downpayment)
        loans = dict(mortgage=mortgage, studentloan=self.studentloan, debt=self.debt)
        assets = dict(income=self.income, wealth=self.wealth - downpayment - closingcost, value=value)
        newfinancials = self.__class__(**assets, **self.rates, **loans) 
        if newfinancials.wealth < 0: raise InsufficientFundsError()  
        if not bank.qualify(newfinancials.coverage): raise InsufficientCoverageError()
        return newfinancials
    
#    def projection(self, duration, *args, wealthrate, incomerate, valuerate, basis='month', **kwargs):  
#        duration = _monthduration[basis](duration)
#        wealthrate, incomerate, valuerate = [_monthrate[basis](rate) for rate in (wealthrate, incomerate, valuerate)]
#        income = self.income * income_compounding(min(duration, self.__incomehorizon), incomerate=incomerate, wealthrate=wealthrate)
#        consumption = self.consumption * consumption_compounding(duration, discountrate=self.discountrate, risktolerance=self.risktolerance, wealthrate=wealthrate)        
#        newwealth = self.wealth * pow(1 + wealthrate, duration) + income - consumption
#        newincome = self.income * pow(1 + incomerate, duration)
#        newvalue = self.value * pow(1 + valuerate, duration)
#        newmortgage = self.mortgage.projection(duration, *args, **kwargs) 
#        newstudentloan = self.studentloan.projection(duration, *args, **kwargs)
#        newdebt = self.debt.projection(duration, *args, **kwargs)
#        loans = dict(mortgage=newmortgage, studentloan=newstudentloan, debt=newdebt)
#        assets = dict(income=newincome, wealth=newwealth, value=newvalue)
#        newfinancials = self.__class__(**assets, **self.rates, **loans)  
#        return newfinancials







