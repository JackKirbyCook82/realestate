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
__all__ = ['createFinancials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_convertKeys = ['year', 'month', 'week']
_convertMatrix = np.array([[1, 12, 52], [-12, 1, 52/12], [-52, -52/12, 1]]) 
_convertindex = lambda key: _convertKeys.index(key)
_convertfactor = lambda fromvalue, tovalue: _convertMatrix[_convertindex(fromvalue), _convertindex(tovalue)]
_convertrate = lambda frombasis, tobasis, rate: pow((1 + rate), _convertfactor(frombasis, tobasis)) - 1
_convertduration = lambda frombasis, tobasis, duration: duration * _convertfactor(frombasis, tobasis)
_convertflow = lambda frombasis, tobasis, duration: duration / _convertfactor(frombasis, tobasis)

theta = lambda risktolerance, discountrate, wealthrate: (wealthrate - discountrate) / risktolerance
wealth_factor = lambda wr, n: pow(1 + wr, n)
value_factor = lambda ar, n: pow(1 + ar, n)
income_factor = lambda ir, wr, n: pow(1 + ir, n) / (ir - wr)
consumption_factor = lambda tr, wr, n: pow(1 + tr, n) / (tr - wr)
loan_factor = lambda lr, wr, n: (lr / wr) * (pow(1 + lr, n) / (1 - pow(1 + lr, n)))
  

def createFinancials(geography, date, *args, ages, **kwargs): 
    start_age = ages['adulthood']
    horizon = max(ages['death'] - start_age, 0)
    incomehorizon = max(ages['retirement'] - start_age, 0)
    money = dict(income=100000, wealth=50000, value=50000)
    loans = dict(mortgage=None, studentloan=None, debt=None)
    kwargs.update(**money, **loans)
    return Financials(horizon, incomehorizon, *args, **kwargs)
 
    
#def createFinancials(geography, date, *args, horizon, age, education, income, value, yearoccupied, economy, **kwargs): 
#    start_school = economy.schools[str(education).lower()]
#    start_age = economy.ages['adulthood'] + start_school.duration     
#    start_year = date.year - age.value - start_school.duration    
#    start_income = income / np.prod(np.array([1 + economy.rates['income'](i, basis='year') for i in range(start_year, date.year)]))
#    start_studentloan = economy.banks['studentloan'].loan(start_school.cost)   
#    assert start_age <= age.value and start_year <= date.year
#    
#    purchase_age = age - date.year - yearoccupied.value
#    purchase_year = yearoccupied.value    
#    purchase_value = value / np.prod(np.array([1 + economy.valuerate(i, basis='year') for i in range(purchase_year,  date.year)]))            
#    purchase_downpayment = economy.banks['mortgage'].downpayment(purchase_value)
#    purchase_cost = economy.banks['mortgage'].cost(purchase_value - purchase_downpayment)
#    purchase_cash = purchase_downpayment - purchase_cost    
#    assert start_year <= purchase_year <= date.year and start_age <= purchase_age <= age.value
#    
#    targets = {purchase_age - start_age:purchase_cash}
#    horizon = max(economy.ages['death'] - start_age, 0)
#    incomehorizon = max(economy.ages['retirement'] - start_age, 0)
#    rates = {'{}rate'.format(key):rate(date.year, basis='month') for key, rate in economy.rates.items()}
#    financials = Financials(horizon, incomehorizon, targets=targets, terminalwealth=0, income=start_income, wealth=0, value=0, mortgage=None, studentloan=start_studentloan, debt=None, **rates)
#    financials = financials.projection(max(purchase_age - start_age, 0), basis='month')
#    financials = financials.buy(purchase_value, bank=economy.banks['mortgage'])
#    financials = financials.projection(max(age.value - purchase_age, 0), basis='month')    
#    return financials   


class InsufficientFundsError(Exception): pass
class InsufficientCoverageError(Exception): pass
class UnstableLifeStyleError(Exception): pass
class ExceededHorizonError(Exception): pass


class Financials(ntuple('Financials', 'income wealth value consumption mortgage studentloan debt')):
    __stringformat = 'Financials|Assets=${assets:.0f}, Debt=${debt:.0f}, Income=${income:.0f}/MO, Consumption=${consumption:.0f}/MO'
    def __str__(self): return self.__stringformat(assets=self.wealth + self.value, income=self.income, debt=self.mortgage.balance + self.studentloan.balance + self.debt.balance, consumption=self.consumption)     
    
    def __repr__(self): 
        content = {'mortgage':repr(self.mortgage), 'studentloan':repr(self.studentloan), 'debt':repr(self.debt)}
        content.update({field:str(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 

    def __new__(cls, duration, incomeduration, *args, targets={}, terminalwealth=0, income, basis='month', **kwargs):        
        duration, incomeduration = [_convertduration(basis, 'month', duration) for duration in (duration, incomeduration)] 
        income = _convertflow(basis, 'month', income)
        targets = {_convertduration(basis, 'month', durationtarget):wealthtarget for durationtarget, wealthtarget in targets.items()}       
        consumption = cls.__consumption(duration, incomeduration, terminalwealth, *args, income=income, basis=basis, **kwargs)  
        instance = super().__new__(cls, income=income, consumption=consumption, **kwargs)   
        for targetduration in reversed(sorted(targets.keys())):            
            if instance.wealth(targetduration, *args, basis='year', **kwargs) + instance.value(targetduration, *args, basis='year', **kwargs) < targets[targetduration]: 
                consumption = cls.__consumption(targetduration, incomeduration, targets[targetduration], *args, basis=basis, **kwargs)  
                instance = super().__new__(cls, consumption=consumption, **kwargs) 
        return instance  

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    @classmethod
    def __consumption(cls, duration, incomeduration, terminalwealth, *args, income, wealth, value, basis='month', **kwargs):                  
        discountrate, wealthrate, incomerate, valuerate = [_convertrate(basis, 'month', kwargs[rate]) for rate in ('discountrate', 'wealthrate', 'incomerate', 'valuerate')]      
        riskrate = kwargs['riskrate']
        mortgage, studentloan, debt = [kwargs.get(loan, None) for loan in ('mortgage', 'studentloan', 'debt')]
        w = wealth_factor(wealthrate, duration)
        a = value_factor(valuerate, duration)
        i = income_factor(incomerate, wealthrate, incomeduration)
        c = consumption_factor(theta(riskrate, discountrate, wealthrate), wealthrate, duration)
        m = loan_factor(mortgage.rate, wealthrate, min(duration, mortgage.duration)) if mortgage is not None else 0
        s = loan_factor(studentloan.rate, wealthrate, min(duration, studentloan.duration)) if studentloan is not None else 0
        d = loan_factor(debt.rate, wealthrate, min(duration, debt.duration)) if debt is not None else 0 
        consumption = (w * wealth + a * value + i * income - m * mortgage.balance - s * studentloan.balance - d * debt.balance - terminalwealth) / c
        if consumption < 0: raise UnstableLifeStyleError()   
        else: return int(consumption)    
     
    def wealth(self, duration, incomeduration, *args, basis='month', **kwargs):
        duration = _convertduration(basis, 'month', duration)        
        discountrate, wealthrate, incomerate, valuerate = [_convertrate(basis, 'month', kwargs[rate]) for rate in ('discountrate', 'wealthrate', 'incomerate', 'valuerate')]    
        riskrate = kwargs['riskrate']        
        w = wealth_factor(wealthrate, duration)        
        i = income_factor(incomerate, wealthrate, incomeduration)
        c = consumption_factor(theta(riskrate, discountrate, wealthrate), wealthrate, duration)
        m = loan_factor(self.mortgage.rate, wealthrate, min(duration, self.mortgage.duration)) if self.mortgage is not None else 0
        s = loan_factor(self.studentloan.rate, wealthrate, min(duration, self.studentloan.duration)) if self.studentloan is not None else 0
        d = loan_factor(self.debt.rate, wealthrate, min(duration, self.debt.duration)) if self.debt is not None else 0    
        return w * self.wealth + i * self.income - c * self.consumption - m * self.mortgage.balance - s * self.studentloan.balance - d * self.debt.balance
    
    def value(self, duration, *args, basis='month', **kwargs):
        duration = _convertduration(basis, 'month', duration) 
        valuerate = _convertrate(basis, 'month', kwargs['valuerate'])
        a = value_factor(valuerate, duration)
        return a * self.value 

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
        newfinancials = self.__class__(*args, **assets, **loans, **kwargs)  
        return newfinancials
    
    def buy(self, value, *args, bank, **kwargs): 
        assert value > 0 and self.value == 0 and self.mortgage is None
        downpayment = bank.downpayment(value)
        closingcost = bank.cost(value - downpayment)
        mortgage = bank.loan(value - downpayment)
        loans = dict(mortgage=mortgage, studentloan=self.studentloan, debt=self.debt)
        assets = dict(income=self.income, wealth=self.wealth - downpayment - closingcost, value=value)
        newfinancials = self.__class__(*args, **assets, **loans, **kwargs) 
        if newfinancials.wealth < 0: raise InsufficientFundsError()  
        if not bank.qualify(newfinancials.coverage): raise InsufficientCoverageError()
        return newfinancials
    
    def projection(self, duration, incomeduration, *args, basis='month', **kwargs):  
        incomerate = _convertrate(basis, 'month', kwargs['incomerate'])
        newwealth = self.wealth(duration, incomeduration, *args, basis=basis, **kwargs)
        newvalue = self.value(duration, *args, basis=basis, **kwargs)       
        duration = _convertduration(basis, 'month', duration)
        newincome = self.income * pow(1 + incomerate, duration)
        newmortgage = self.mortgage.projection(duration, *args, **kwargs) if self.mortgage is not None else None
        newstudentloan = self.studentloan.projection(duration, *args, **kwargs) if self.studentloan is not None else None
        newdebt = self.debt.projection(duration, *args, **kwargs) if self.debt is not None else None
        loans = dict(mortgage=newmortgage, studentloan=newstudentloan, debt=newdebt)
        assets = dict(income=newincome, wealth=newwealth, value=newvalue)
        newfinancials = self.__class__(*args, **assets, **loans, **kwargs)  
        return newfinancials









