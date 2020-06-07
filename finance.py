# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['createFinancials', 'Financials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


theta = lambda dr, wr, risk: (wr - dr) / risk
pad = lambda *xns: max([len(xn) for xn in xns])

loanvalue = lambda x, r, n, i: np.fv(r, i, -np.pmt(r, n, x), -x)
flowvalue = lambda x, r, i: np.fv(r, i, 0, -x)
assetvalue = lambda x, r, i: np.fv(r, i, 0, -x)

narray = lambda n: np.arange(n+1)
imatrix = lambda n: np.triu(-np.subtract(*np.mgrid[0:n, 0:n]))
rmatrix = lambda r, n: np.ones((n,n)) * (1+r)
fmatrix = lambda r, n: np.triu(rmatrix(r, n) ** imatrix(n))

loanarray = lambda x, r, n: np.fv(r, narray(n), -np.pmt(r, n, x), -x)
flowarray = lambda x, r, n: np.fv(r, narray(n), 0, -x)
assetarray = lambda x, r, n: np.fv(r, narray(n), 0, -x)
payarray = lambda x, r, n: np.concatenate([np.array([0]), -np.ones(n) * np.pmt(r, n, x)])
investarray = lambda xn, r: np.sum(fmatrix(r, len(xn)) * np.expand_dims(xn, 1), axis=0)

addarrays = lambda *xns: sum(xns)
padarrays = lambda *xns: [np.pad(xn, (0, max(pad(*xns)-len(xn), 0)), mode='constant') for xn in xns]


def createFinancials(geography, date, *args, age, education, yearoccupied, income, value, rates, ages, educations, banks, **kwargs):
    pass

#    school = educations[str(education).lower()] 
#    studentloan = banks['studentloan'].loan(school.cost)  
#    ratevalues ={key:value(date.year, units='month') for key, value in rates.items()}      
#    
#    start_age = int(ages['adulthood'] + (school.duration/12))   
#    occupied_age = int(age) - (int(date.year) - int(yearoccupied))
#    current_age = int(age)
#    retirement_age = ages['retirement']
#    death_age = ages['death']
#    assert start_age <= occupied_age <= current_age <= death_age
#
#    start_year = int(date.year - (int(age) - start_age))  
#    occupied_year = int(yearoccupied)
#    current_year = int(date.year)
#    retirement_year = int(date.year + (retirement_age - int(age)))
#    death_year = int(date.year + (death_age - int(age)))
#    assert start_year <= occupied_year <= current_year <= death_year
#    
#    income_horizon = max(int((retirement_year - start_year) * 12), 0)
#    consumption_horizon = int((death_year - start_year) * 12)
#    income = int(income) / np.prod(np.array([1 + rates['incomerate'](i, units='year') for i in range(start_year, current_year)]))    
#    financials = Financials.fromLifeTime(income_horizon, consumption_horizon, *args, income=income, studentloan=studentloan, **ratevalues, **kwargs) 
#    yield financials
#    
#    horizon = int((occupied_year - start_year) * 12)
#    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)
#    financials.purchase(int(value), bank=banks['mortgage'])
#    yield financials
#
#    horizon = int((current_year - occupied_year) * 12)
#    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)
#    yield financials
#    
#    horizon = int((retirement_year - current_year) * 12) 
#    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)
#    yield financials
#
#    horizon = int((death_year - retirement_year) * 12) 
#    financials = financials.projection(horizon, *args, **ratevalues, **kwargs)    
#    yield financials
  

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
        content.update({'loans':sum([value.balance if value is not None else 0 for value in self.loans.values()])})        
        return self.__stringformat.format(**content)     
    
    def __repr__(self): 
        content = {'incomehorizon':str(self.incomehorizon), 'consumptionhorizon':str(self.consumptionhorizon)}
        content.update({key:str(round(value, ndigits=1)) for key, value in self.assets.items()})
        content.update({key:str(round(value, ndigits=1)) for key, value in self.flows.items()})
        content.update({key:repr(value) if value is not None else None for key, value in self.loans.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 
    
    def __new__(cls, income_horizon , consumption_horizon, *args, income, wealth, value, consumption, mortgage=None, studentloan=None, **kwargs):        
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        return super().__new__(cls, int(income_horizon), int(consumption_horizon), income, wealth, value, consumption, mortgage, studentloan)   

    @property
    def assets(self): return dict(wealth=self.wealth, value=self.value)
    @property
    def flows(self): return dict(income=self.income, consumption=self.consumption)
    @property
    def loans(self): return dict(mortgage=self.mortgage, studentloan=self.studentloan) 

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    def projection(self, *args, discountrate, wealthrate, valuerate, incomerate, risktolerance, **kwargs):       
        mortgage = loanarray(self.mortgage.balance, self.mortgage.rate, self.mortgage.duration)
        studentloan = loanarray(self.studentloan.balance, self.studentloan.rate, self.studentloan.duration)
        income = flowarray(self.income, incomerate, self.incomehorizon)
        consumption = flowarray(self.consumption, theta(discountrate, wealthrate, risktolerance), self.consumptionhorizon)
        value = assetarray(self.value, valuerate, self.consumptionhorizon)
        mortgagepayments = payarray(self.mortgage.balance, self.mortgage.rate, self.mortgage.duration)
        studentloanpayments = payarray(self.studentloan.balance, self.studentloan.rate, self.studentloan.duration)        
        income, consumption, mortgagepayments, studentloanpayments = padarrays(income, consumption, mortgagepayments, studentloanpayments)
        savings = addarrays(income, -consumption, -mortgagepayments, -studentloanpayments)
        cashflows = np.concatenate([np.array([self.wealth]), savings])
        wealth = investarray(cashflows, wealthrate)[:-1]
        income, consumption, wealth, value, mortgage, studentloan = padarrays(income, consumption, wealth, value, mortgage, studentloan) 
        data = {'Income':income, 'Consumption':consumption, 'Wealth':wealth, 'Value':value, 'Mortgage':mortgage, 'Studentloan':studentloan}
        dataframe = pd.DataFrame(data)
        dataframe.index.name = 'Horizon'
        dataframe.name = 'Financials'
        return dataframe

    def __call__(self, horizon, *args, discountrate, wealthrate, valuerate, incomerate, risktolerance, **kwargs):
        assert isinstance(horizon, int) and horizon <= self.consumptionhorizon
        income = flowvalue(self.income, incomerate, min(horizon, self.incomehorizon)) 
        consumption = flowvalue(self.consumption, theta(discountrate, wealthrate, risktolerance), horizon) 
        mortgage = self.mortgage(horizon) if self.mortgage else None
        studentloan = self.studentloan(horizon) if self.studentloan else None
        value = assetvalue(self.value, valuerate, horizon) 
        incomearray = flowarray(self.income, incomerate, self.incomehorizon)
        consumptionarray = flowarray(self.consumption, theta(discountrate, wealthrate, risktolerance), self.consumptionhorizon)
        mortgagepayments = payarray(self.mortgage.balance, self.mortgage.rate, self.mortgage.duration)
        studentloanpayments = payarray(self.studentloan.balance, self.studentloan.rate, self.studentloan.duration)        
        incomearray, consumptionarray, mortgagepayments, studentloanpayments = padarrays(incomearray, consumptionarray, mortgagepayments, studentloanpayments)
        savings = addarrays(incomearray, -consumptionarray, -mortgagepayments, -studentloanpayments)       
        cashflows = np.concatenate([np.array([self.wealth]), savings])
        wealth = investarray(cashflows, wealthrate)[horizon]
        consumptionhorizon = self.consumptionhorizon - horizon 
        incomehorizon = max(self.incomehorizon - horizon, 0)
        assets = dict(wealth=wealth, value=value)
        flows = dict(income=income, consumption=consumption)
        loans = dict(mortgage=mortgage, studentloan=studentloan)
        return self.__class__(consumptionhorizon, incomehorizon, **assets, **flows, **loans)
        
    def sale(self, *args, broker, **kwargs):
        assert self.value > 0
        proceeds = self.value - broker.cost(self.value) - (self.mortgage.balance if self.mortgage else 0)
        assets = dict(wealth=self.wealth + proceeds, value=0)
        flows = dict(income=self.income, consumption=self.consumption)
        loans = dict(mortgage=None, studentloan=self.studentloan)
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

#    @classmethod
#    def fromLifeTime(cls, income_horizon, consumption_horizon, *args, income, studentloan, wealth=0, terminalwealth=0, risktolerance, discountrate, incomerate, wealthrate, **kwargs):
#        w = wealth_factor(wealthrate, consumption_horizon)
#        i = income_factor(incomerate, wealthrate, min(consumption_horizon, income_horizon))
#        c = consumption_factor(theta(discountrate, wealthrate, risktolerance), wealthrate, consumption_horizon)
#        x = loan_factor(wealthrate, min(consumption_horizon, studentloan.duration))
#        consumption = (w * wealth - terminalwealth + i * income - x * studentloan.payment) / c      
#        return Financials(income=income, wealth=wealth, value=0, consumption=consumption, studentloan=studentloan)    
 







