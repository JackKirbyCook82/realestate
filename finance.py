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

theta = lambda risktolerance, discountrate, wealthrate: (wealthrate - discountrate) / risktolerance
wealth_factor = lambda wr, n: pow(1 + wr, n)
value_factor = lambda ar, n: pow(1 + ar, n)
income_factor = lambda ir, wr, n: pow(1 + ir, n) / (ir - wr)
consumption_factor = lambda tr, wr, n: pow(1 + tr, n) / (tr - wr)
loan_factor = lambda lr, wr, n: (lr / wr) * (pow(1 + lr, n) / (1 - pow(1 + lr, n)))
  

class InsufficientFundsError(Exception): pass
class InsufficientCoverageError(Exception): pass
class UnstableLifeStyleError(Exception): pass
class ExceededHorizonError(Exception): pass


class Financials(ntuple('Financials', 'horizon incomehorizon discountrate risktolerance income wealth value consumption mortgage studentloan debt')):
    stringformat = 'Financials|Assets=${assets:.0f}, Debt=${debt:.0f}, Income=${income:.0f}/MO'
    def __str__(self): return self.stringformat(assets=self.wealth + self.value, income=self.income, debt=self.mortgage.balance + self.studentloan.balance + self.debt.balance)     
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, repr(self[field])]) for field in self._fields]))  
    def __hash__(self): return hash((self.__class__.__name__, self.horizon, self.discountrate, self.risktolerance, self.income, self.wealth, self.value, self.consumption, hash(self.mortgage), hash(self.studentloan), hash(self.debt),))    

    def __new__(cls, horizonduration, incomeduration, *args, targets={}, terminalwealth=0, basis='month', **kwargs):        
        kwargs.update({'discountrate':_monthrate(kwargs['discountrate']), 'income':_monthflow(kwargs['income'])})
        targets = {_monthduration[basis](duration):wealthtarget for duration, wealthtarget in targets.keys()}
        horizon, incomehorizon, consumption = horizonduration, incomeduration, cls.__consumption(horizonduration, incomeduration, terminalwealth, *args, basis=basis, **kwargs)  
        instance = super().__new__(cls, horizon=horizon, incomehorizon=incomehorizon, consumption=consumption, **kwargs)   
        for targetduration in reversed(sorted(targets.keys())):            
            if instance.wealth(targetduration, *args, basis='year', **kwargs) + instance.value(targetduration, *args, basis='year', **kwargs) < targets[targetduration]: 
                horizon, consumption = targetduration, cls.__consumption(targetduration, incomeduration, targets[targetduration], *args, basis=basis, **kwargs)  
                instance = super().__new__(cls, horizon=horizon, consumption=consumption, **kwargs) 
        return instance  

    @classmethod
    def __consumption(cls, horizonduration, incomeduration, terminalwealth, *args, discountrate, risktolerance, income, wealth, value, basis='month', **kwargs):
        horizonduration, incomeduration = [_monthduration[basis](kwargs[rate]) for rate in (horizonduration, incomeduration)]   
        wealthrate, incomerate, valuerate = [_monthrate[basis](kwargs[rate]) for rate in ('wealthrate', 'incomerate', 'valuerate')]      
        mortgage, studentloan, debt = [kwargs.get(loan, None) for loan in ('mortgage', 'studentloan', 'debt')]
        w = wealth_factor(wealthrate, horizonduration)
        a = value_factor(valuerate, horizonduration)
        i = income_factor(incomerate, wealthrate, incomeduration)
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizonduration)
        m = loan_factor(mortgage.rate, wealthrate, min(horizonduration, mortgage.duration)) if mortgage is not None else 0
        s = loan_factor(studentloan.rate, wealthrate, min(horizonduration, studentloan.duration)) if studentloan is not None else 0
        d = loan_factor(debt.rate, wealthrate, min(horizonduration, debt.duration)) if debt is not None else 0 
        consumption = (w * wealth + a * value + i * income - m * mortgage.balance - s * studentloan.balance - d * debt.balance - terminalwealth) / c
        if consumption < 0: raise UnstableLifeStyleError()   
        else: return horizonduration, int(consumption)    
     
    def wealth(self, duration, *args, basis='month', **kwargs):
        if duration > self.__horizonduration: raise ExceededHorizonError()
        duration = _monthduration[basis](kwargs[duration]) 
        wealthrate, incomerate, valuerate = [_monthrate[basis](kwargs[rate]) for rate in ('wealthrate', 'incomerate', 'valuerate')]              
        w = wealth_factor(wealthrate, duration)        
        i = income_factor(incomerate, wealthrate, self.incomeduration)
        c = consumption_factor(theta(self.risktolerance, self.discountrate, wealthrate), wealthrate, duration)
        m = loan_factor(self.mortgage.rate, wealthrate, min(duration, self.mortgage.duration)) if self.mortgage is not None else 0
        s = loan_factor(self.studentloan.rate, wealthrate, min(duration, self.studentloan.duration)) if self.studentloan is not None else 0
        d = loan_factor(self.debt.rate, wealthrate, min(duration, self.debt.duration)) if self.debt is not None else 0    
        return w * self.wealth + i * self.income - c * self.consumption - m * self.mortgage.balance - s * self.studentloan.balance - d * self.debt.balance
    
    def value(self, duration, *args, valuerate, basis='month', **kwargs):
        if duration > self.__horizonduration: raise ExceededHorizonError()
        duration = _monthduration[basis](kwargs[duration])
        valuerate = _monthrate[basis](kwargs[valuerate])   
        a = value_factor(valuerate, duration)
        return a * self.value 
    
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
        loans = dict(mortgage=self.mortgage.payoff() if self.mortgage is not None else None, studentloan=self.studentloan, debt=self.debt)
        assets = dict(income=self.income, wealth=self.wealth + proceeds, value=0)
        newfinancials = self.__class__(**assets, **self.rates, **loans)  
        return newfinancials
    
    def buy(self, value, *args, bank, **kwargs): 
        assert value > 0 and self.value == 0 and self.mortgage is None
        downpayment = bank.downpayment(value)
        closingcost = bank.cost(value - downpayment)
        mortgage = bank.loan(value - downpayment)
        loans = dict(mortgage=mortgage, studentloan=self.studentloan, debt=self.debt)
        assets = dict(income=self.income, wealth=self.wealth - downpayment - closingcost, value=value)
        newfinancials = self.__class__(**assets, **self.rates, **loans) 
        if newfinancials.wealth < 0: raise InsufficientFundsError()  
        if not bank.qualify(newfinancials.coverage): raise InsufficientCoverageError()
        return newfinancials
    
    def projection(self, duration, *args, basis='month', **kwargs):  
        newwealth = self.wealth(duration, *args, basis=basis, **kwargs)
        newvalue = self.value(duration, *args, basis=basis, **kwargs)       
        duration = _monthduration[basis](kwargs[duration])
        wealthrate, incomerate, valuerate = [_monthrate[basis](kwargs[rate]) for rate in ('wealthrate', 'incomerate', 'valuerate')]   
        newincome = self.income * pow(1 + incomerate, duration)
        newmortgage = self.mortgage.projection(duration, *args, **kwargs) if self.mortgage is not None else None
        newstudentloan = self.studentloan.projection(duration, *args, **kwargs) if self.studentloan is not None else None
        newdebt = self.debt.projection(duration, *args, **kwargs) if self.debt is not None else None
        loans = dict(mortgage=newmortgage, studentloan=newstudentloan, debt=newdebt)
        assets = dict(income=newincome, wealth=newwealth, value=newvalue)
        newfinancials = self.__class__(**assets, **self.rates, **loans)  
        return newfinancials

#    @classmethod
#    def create(cls, year, *args, discountrate, risktolerance, age, education, value, yearoccupied, income, ages, schools, economy, banks, **kwargs):
#        start_school = schools[education]
#        start_age = ages['adulthood'] + start_school.duration     
#        start_year = year - age - start_school.duration    
#        start_income = income / np.prod(np.array([1 + economy.incomerate(i, basis='year') for i in range(start_year, year)]))
#        start_studentloan = banks['studentloan'].loan(start_school.cost)   
#        assert start_age <= age and start_year <= year
#        
#        purchase_age = age - year - yearoccupied
#        purchase_year = yearoccupied    
#        purchase_value = value / np.prod(np.array([1 + economy.valuerate(i, basis='year') for i in range(purchase_year, year)]))            
#        purchase_downpayment = banks['mortgage'].downpayment(purchase_value)
#        purchase_cost = banks['mortgage'].cost(purchase_value - purchase_downpayment)
#        purchase_cash = purchase_downpayment - purchase_cost    
#        assert start_year <= purchase_year <= year and start_age <= purchase_age <= age
#        
#        targets = {purchase_age - start_age:purchase_cash}
#        financials = cls(max(ages['death'] - start_age, 0), max(ages['retirement'] - start_age, 0), targets=targets, terminalwealth=0, discountrate=discountrate, risktolerance=risktolerance, 
#                         income=start_income, wealth=0, value=0, mortgage=None, studentloan=start_studentloan, debt=None, **economy.rates(year, basis='year'), basis='year')
#        financials = financials.projection(max(purchase_age - start_age, 0), **economy.rates(year, basis='year'), basis='year')
#        financials = financials.buy(purchase_value, bank=banks['mortgage'])
#        financials = financials.projection(max(age - purchase_age, 0), **economy.rates(year, basis='year'), basis='year')    
#        return financials












