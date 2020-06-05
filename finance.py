# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
from collections import namedtuple as ntuple

from realestate.economy import Loan

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['createFinancials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


iarray = lambda n: np.arange(n)
rarray = lambda r, n: np.ones(n) * r
farray = lambda r, n: rarray(r, n) ** iarray(n)
dotarray = lambda x, y: np.dot(x, y)

imatrix = lambda n: np.triu(-np.subtract(*np.mgrid[0:n, 0:n]))
rmatrix = lambda r, n: np.ones((n,n)) * r
fmatrix = lambda r, n: np.triu(rmatrix(r, n) ** imatrix(n))

theta = lambda dr, wr, risk: (wr - dr) / risk
wealth_factor = lambda wr, n: farray(1 + wr, n).sum()[()]
income_factor = lambda ir, wr, n: dotarray(farray(1 + ir, n-1), farray(1 + wr, n-1)[::-1])[()]
consumption_factor = lambda cr, wr, n: dotarray(farray(1 + cr, n-1), farray(1 + wr, n-1)[::-1])[()]
loan_factor = lambda wr, n: farray(1 + wr, n-1).sum()[()]


def createFinancials(geography, date, *args, age, education, yearoccupied, income, value, rates, ages, educations, banks, **kwargs):
    school = educations[str(education).lower()] 
    studentloan = banks['studentloan'].loan(school.cost)  
    ratevalues ={key:value(date.year, units='month') for key, value in rates.items()}      
    
    start_age = int(ages['adulthood'] + (school.duration/12))   
    occupied_age = int(age) - (int(date.year) - int(yearoccupied))
    current_age = int(age)
    retirement_age = ages['retirement']
    death_age = ages['death']
    assert start_age <= occupied_age <= current_age <= death_age

    start_year = int(date.year - (int(age) - start_age))  
    occupied_year = int(yearoccupied)
    current_year = int(date.year)
    retirement_year = int(date.year + (retirement_age - int(age)))
    death_year = int(date.year + (death_age - int(age)))
    assert start_year <= occupied_year <= current_year <= death_year
    
    income_horizon = max(int((retirement_year - start_year) * 12), 0)
    consumption_horizon = int((death_year - start_year) * 12)
    income = int(income) / np.prod(np.array([1 + rates['incomerate'](i, units='year') for i in range(start_year, current_year)]))    
    financials = Financials.fromLifeTime(income_horizon, consumption_horizon, *args, income=income, studentloan=studentloan, **ratevalues, **kwargs) 
    yield financials
    
    horizon = int((occupied_year - start_year) * 12)
    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)
    financials.purchase(int(value), bank=banks['mortgage'])
    yield financials

    horizon = int((current_year - occupied_year) * 12)
    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)
    yield financials
    
    horizon = int((retirement_year - current_year) * 12) 
    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)
    yield financials

    horizon = int((death_year - retirement_year) * 12) 
    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)    
    yield financials
  

class UnsolventLifeStyleError(Exception): 
    @property
    def wealth(self): return self.__wealth
    def __str__(self): return super().__str__('${}'.format(self.wealth))
    def __init__(self, wealth): 
        assert wealth < 0
        self.__wealth = int(abs(wealth))
        super().__init__()
    
class UnstableLifeStyleError(Exception): 
    @property
    def consumption(self): return self.__consumption
    def __str__(self): return super().__str__('-${}/MO'.format(self.deficit))    
    def __init__(self, consumption): 
        assert consumption < 0
        self.__consumption = int(abs(consumption))
        super().__init__()

class InsufficientFundsError(Exception): 
    @property
    def wealth(self): return self.__wealth
    def __str__(self): return super().__str__('${}'.format(self.wealth))
    def __init__(self, wealth): 
        assert wealth < 0
        self.__wealth = int(abs(wealth))
        super().__init__()

class InsufficientCoverageError(Exception):
    @property
    def coverage(self): return self.__coverage
    @property
    def required(self): return self.__required
    def __str__(self): return super().__str__('{:.2f} < {:.2f}'.format(self.coverage, self.requiredcoverage)) 
    def __init__(self, coverage, required): 
        self.__coverage, self.__required = coverage, required
        super().__init__()


class Financials(ntuple('Financials', 'incomehorizon consumptionhorizon income wealth value consumption mortgage studentloan')):
    __stringformat = 'Financials[{horizon}]|Assets=${assets:.0f}, Loans=${loans:.0f}, Income=${income:.0f}/MO, Consumption=${consumption:.0f}/MO'
    def __str__(self): 
        content = {**self.flows, 'horizon':self.consumptionhorizon}
        content.update({'assets':sum([value for value in self.assets.values()])})
        content.update({'loans':sum([value.balance for value in self.loans.values()])})        
        return self.__stringformat.format(**content)     
    
    def __repr__(self): 
        content = {'incomehorizon':self.incomehorizon, 'consumptionhorizon':self.consumptionhorizon}
        content.update({key:str(int(value)) for key, value in self.assets.items()})
        content.update({key:str(int(value)) for key, value in self.flows.items()})
        content.update({key:repr(value) for key, value in self.loans.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 
    
    def __new__(cls, income_horizon , consumption_horizon, *args, income, wealth, value, consumption, mortgage=None, studentloan=None, **kwargs):        
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        mortgage = mortgage if mortgage is not None else Loan('mortgage', balance=0, rate=0, duration=0, basis='month')
        studentloan = studentloan if studentloan is not None else Loan('studentloan', balance=0, rate=0, duration=0, basis='month')
        return super().__new__(cls, int(income_horizon), int(consumption_horizon), income, wealth, value, consumption, mortgage, studentloan)   

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    @property
    def assets(self): return dict(wealth=self.wealth, value=self.value)
    @property
    def flows(self): return dict(income=self.income, consumption=self.consumption)
    @property
    def loans(self): return dict(mortgage=self.mortgage, studentloan=self.studentloan) 

    def sale(self, *args, broker, **kwargs):
        proceeds = self.value - broker.cost(self.value) - self.mortgage.balance 
        assets = dict(wealth=self.wealth + proceeds, value=0)
        flows = dict(income=self.income, consumption=self.consumption)
        loans = dict(mortgage=self.mortgage.payoff(), studentloan=self.studentloan)
        return self.__class__(**assets, **flows, **loans)

    def purchase(self, value, *args, bank, **kwargs):
        if value == 0: return self
        assert value > 0 and self.value == 0 and not self.mortgage
        downpayment = bank.downpayment(value)
        closingcost = bank.cost(value - downpayment)
        wealth = self.wealth - downpayment - closingcost
        mortgage = bank.loan(value - downpayment)   
        coverage = self.income / (self.studentloan.payment + mortgage.payment)        
        if wealth < 0: raise InsufficientFundsError(wealth)       
        if coverage < bank.coverage: raise InsufficientCoverageError(coverage, bank.coverage)
        assets = dict(income=self.income, wealth=wealth, value=self.value)
        flows = dict(income=self.income, consumption=self.consumption)
        loans = dict(mortgage=mortgage, studentloan=self.studentloan)
        return self.__class__(**assets, **flows, **loans)
        
    @classmethod
    def fromLifeTime(cls, income_horizon, consumption_horizon, *args, income, studentloan, wealth=0, terminalwealth=0, risktolerance, discountrate, incomerate, wealthrate, **kwargs):
        w = wealth_factor(wealthrate, consumption_horizon)
        i = income_factor(incomerate, wealthrate, min(consumption_horizon, income_horizon))
        c = consumption_factor(theta(discountrate, wealthrate, risktolerance), wealthrate, consumption_horizon)
        x = loan_factor(wealthrate, min(consumption_horizon, studentloan.duration))
        consumption = (w * wealth - terminalwealth + i * income - x * studentloan.payment) / c      
        return Financials(income=income, wealth=wealth, value=0, consumption=consumption, studentloan=studentloan)    
 
    def income_projection(self, horizon, *args, incomerate, **kwargs):
        x = farray(1 + incomerate, min(horizon, self.incomehorizon, self.consumptionhorizon)+1)
        pad = min(horizon, self.consumptionhorizon) - self.incomehorizon
        return  np.pad(x, (0, pad), 'constant') * self.income
        
    def consumption_projection(self, horizon, *args, risktolerance, discountrate, wealthrate, **kwargs):
        consumptionrate = theta(discountrate, wealthrate, risktolerance)
        return farray(1 + consumptionrate, min(horizon, self.consumptionhorizon)+1) * self.consumption

    def saving_projection(self, horizon, *args, **kwargs):
        incomes = self.income_projection(horizon, *args, **kwargs)
        consumptions = self.consumption_projection(horizon, *args, **kwargs)
        return incomes - consumptions

    def cashflow_projection(self, horizon, *args, **kwargs):
        cashflow = self.saving_projection(horizon, *args, **kwargs)[:-1]
        return np.concatenate([np.array([self.wealth]), cashflow])
            
    def wealth_projection(self, horizon, *args, wealthrate, **kwargs):        
        cashflow = self.cashflow_projection(horizon, *args, wealthrate=wealthrate, **kwargs)
        return np.cumsum(np.sum(np.multiply(fmatrix(wealthrate, min(horizon, self.consumptionhorizon)+1), cashflow), axis=0))

    def value_projection(self, horizon, *args, valuerate, **kwargs): return farray(1 + valuerate, min(horizon, self.consumptionhorizon)+1) * self.value
    def mortgage_projection(self, horizon, *args, **kwargs): return self.mortgage.projection(min(horizon, self.consumptionhorizon))
    def studentloan_projection(self, horizon, *args, **kwargs): return self.studentloan.projection(min(horizon, self.consumptionhorizon))       
    
#    def income_projection(self, horizon, incomerate): 
#        if horizon > self.incomehorizon: return 0
#        else: return self.income * projection_factor(incomerate, horizon)
#        
#    def consumption_projection(self, horizon, risktolerance, discountrate, wealthrate):
#        return self.consumption * projection_factor(theta(discountrate, wealthrate, risktolerance), horizon)    
#    
#    def value_projection(self, horizon, valuerate): return self.value * projection_factor(valuerate, horizon)    
#    def mortgage_projection(self, horizon): return self.mortgage.projection(horizon)    
#    def studentloan_projection(self, horizon): return self.studentloan.projection(horizon)    
    
#    def wealth_projection(self, horizon, risktolerance, discountrate, wealthrate, incomerate): 
#        w = wealth_factor(wealthrate, horizon)
#        i = income_factor(incomerate, wealthrate, min(horizon, self.incomehorizon))
#        c = consumption_factor(theta(discountrate, wealthrate, risktolerance), wealthrate, horizon)
#        m = loan_factor(wealthrate, min(horizon, self.mortgage.duration)) if self.mortgage else 0
#        s = loan_factor(wealthrate, min(horizon, self.studentloan.duration)) if self.studentloan else 0
#        return  w * self.wealth + i * self.income - c * self.consumption - m * self.mortgage.payment - s * self.studentloan.payment

#    def projection(self, horizon, *args, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):     
#        assert horizon <= self.consumptionhorizon
#        incomehorizon = max(self.incomehorizon - horizon, 0)
#        consumptionhorizon = self.consumptionhorizon - horizon
#        income = self.income_projection(horizon, incomerate)
#        wealth = self.wealth_projection(horizon, risktolerance, discountrate, wealthrate, incomerate)
#        value = self.value_projection(horizon, valuerate)
#        consumption = self.consumption_projection(horizon, risktolerance, discountrate, wealthrate)
#        mortgage = self.mortgage_projection(horizon) 
#        studentloan = self.studentloan_projection(horizon)
#        assets = dict(wealth=wealth, value=value)
#        flows = dict(income=income, consumption=consumption)
#        loans = dict(mortgage=mortgage, studentloan=studentloan)
#        return self.__class__(incomehorizon, consumptionhorizon, **assets, **flows, **loans)

#    def projection(self, horizon, *args, **kwargs):
#        incomes = self.income_projection(horizon, *args, **kwargs)
#        consumptions = self.consumption_projection(horizon, *args, **kwargs)
#        wealths = self.wealth_projection(horizon, *args, **kwargs)
#        values = self.value_projection(horizon, *args, **kwargs)
#        mortgage = self.mortgage_projection(horizon, *args, **kwargs)
#        studentloan = self.studentloan_projection(horizon, *args, **kwargs)
#        assert len(incomes) == len(consumptions) == len(wealths) == len(values) == len(mortgage) == len(studentloan) 

