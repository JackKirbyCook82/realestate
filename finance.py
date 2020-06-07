# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from utilities.strings import uppercase

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
wealth_factor = lambda wr, n: pow(1 + wr, n)
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
  

class ExceededHorizonError(Exception): pass

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
        content = {'incomehorizon':str(self.incomehorizon), 'consumptionhorizon':str(self.consumptionhorizon)}
        content.update({key:str(round(value, ndigits=1)) for key, value in self.assets.items()})
        content.update({key:str(round(value, ndigits=1)) for key, value in self.flows.items()})
        content.update({key:repr(value) for key, value in self.loans.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 
    
    def __new__(cls, income_horizon , consumption_horizon, *args, income, wealth, value, consumption, mortgage=None, studentloan=None, **kwargs):        
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        mortgage = mortgage if mortgage is not None else Loan('mortgage', balance=0, rate=0, duration=0, basis='month')
        studentloan = studentloan if studentloan is not None else Loan('studentloan', balance=0, rate=0, duration=0, basis='month')
        return super().__new__(cls, int(income_horizon), int(consumption_horizon), income, wealth, value, consumption, mortgage, studentloan)   

#    def __call__(self, horizon, *args, risktolerance, incomerate, valuerate, wealthrate, discountrate, **kwargs):
#        if horizon >= self.consumptionhorizon: raise ExceededHorizonError(horizon - self.consumptionhorizon)
#        assert isinstance(horizon, int) and horizon > 0
#        consumptionhorizon = self.consumptionhorizon - horizon
#        incomehorizon =  max(self.incomehorizon - horizon, 0)
#
#        income = self.income * pow(1 + incomerate, min(self.incomehorizon, horizon))
#        consumption = self.consumption * pow(1 + theta(discountrate, wealthrate, risktolerance), min(self.consumptionhorizon, horizon))
#        value = self.value * pow(1 + valuerate, min(self.consumptionhorizon, horizon))        
#        mortgage = self.mortgage(horizon)
#        studentloan = self.studentloan(horizon)        
#        wealth = self.wealth_projection(horizon, *args, risktolerance=risktolerance, incomerate=incomerate, wealthrate=wealthrate, discountrate=discountrate, **kwargs)[horizon]
#        
#        assets = dict(wealth=wealth, value=value)
#        flows = dict(income=income, consumption=consumption)
#        loans = dict(mortgage=mortgage, studentloan=studentloan)        
#        return self.__class__(incomehorizon, consumptionhorizon, **assets, **flows, **loans)
#
#    def todict(self): return self._asdict()
#    def __getitem__(self, item): 
#        if isinstance(item, (int, slice)): return super().__getitem__(item)
#        elif isinstance(item, str): return getattr(self, item)
#        else: raise TypeError(type(item))

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
        assets = dict(wealth=wealth, value=self.value)
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
 
    @keydispatcher
    def get_projection(self, key, horizon, *args, **kwargs): raise KeyError(key)
    def projection(self, horizon, *args, **kwargs):
        assert isinstance(horizon, int) and horizon >= 0
        data = {key:function(self, horizon, *args, **kwargs) for key, function in self.get_projection.registry().items()}
        dataframe = pd.DataFrame(data)
        dataframe.columns = [uppercase(column) for column in dataframe.columns]
        dataframe.index.name = 'Horizon'
        dataframe.name = 'Financials'
        return dataframe
  
    @get_projection.register('income')
    def income_projection(self, horizon, *args, incomerate, **kwargs):
        assert isinstance(horizon, int) and horizon >= 0
        x = farray(1 + incomerate, min(horizon+1, self.incomehorizon+1, self.consumptionhorizon+1))
        pad = self.incomehorizon+1 - min(horizon+1, self.consumptionhorizon+1)
        if pad < 0: x = np.pad(x, (0, -pad), 'constant')
        return x * self.income
    
    @get_projection.register('consumption')       
    def consumption_projection(self, horizon, *args, risktolerance, discountrate, wealthrate, **kwargs):
        assert isinstance(horizon, int) and horizon >= 0
        consumptionrate = theta(discountrate, wealthrate, risktolerance)
        return farray(1 + consumptionrate, min(horizon+1, self.consumptionhorizon+1)) * self.consumption
    
    @get_projection.register('value')
    def value_projection(self, horizon, *args, valuerate, **kwargs):
        assert isinstance(horizon, int) and horizon >= 0
        return farray(1 + valuerate, min(horizon+1, self.consumptionhorizon+1)) * self.value    
    
    @get_projection.register('savings')
    def saving_projection(self, horizon, *args, **kwargs):
        assert isinstance(horizon, int) and horizon >= 0
        incomes = self.income_projection(horizon, *args, **kwargs)
        consumptions = self.consumption_projection(horizon, *args, **kwargs)
#        mortgagepayments  = np.concatenate([np.array([0]), np.ones(min(horizon, self.mortgage.duration)) * self.mortgage.payment])
#        mortgagepad = self.mortgage.duration - min(horizon, self.consumptionhorizon)
#        if mortgagepad < 0: mortgagepayments = np.pad(mortgagepayments, (0, -mortgagepad), 'constant')
#        studentloanpayments = np.concatenate([np.array([0]), np.ones(min(horizon, self.studentloan.duration)) * self.studentloan.payment])
#        studentloanpad = self.studentloan.duration - min(horizon, self.consumptionhorizon)
#        if studentloanpad < 0: studentloanpayments = np.pad(studentloanpayments, (0, -studentloanpad), 'constant')
        return incomes - consumptions

    @get_projection.register('cashflow')
    def cashflow_projection(self, horizon, *args, **kwargs):
        assert isinstance(horizon, int) and horizon >= 0
        cashflow = self.saving_projection(horizon, *args, **kwargs)[:-1]
        return np.concatenate([np.array([self.wealth]), cashflow])    
    

    

