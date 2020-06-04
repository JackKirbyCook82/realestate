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

theta = lambda dr, wr, risk: (wr - dr) / risk
projection_factor = lambda r, n: pow(1 + r, n)
wealth_factor = lambda wr, n: farray(1 + wr, n).sum()[()]
income_factor = lambda ir, wr, n: dotarray(farray(1 + ir, n-1), farray(1 + wr, n-1)[::-1])[()]
consumption_factor = lambda cr, wr, n: dotarray(farray(1 + cr, n-1), farray(1 + wr, n-1)[::-1])[()]
loan_factor = lambda wr, n: farray(1 + wr, n-1).sum()[()]    


def createFinancials(geography, date, *args, age, education, yearoccupied, income, value, rates, ages, educations, banks, **kwargs):
    rate_values = {key:value(date.year, units='month') for key, value in rates.items()}
    start_school = educations[str(education).lower()] 
            
    start_age = int(ages['adulthood'] + (start_school.duration/12))   
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
    
    start_horizon = int((death_year - start_year) * 12)
    start_incomehorizon = max(int((retirement_year - start_year) * 12), 0)
    start_studentloan = banks['studentloan'].loan(start_school.cost)    
    start_income = int(income) / np.prod(np.array([1 + rates['incomerate'](i, units='year') for i in range(start_year, current_year)]))
    financials = Financials.fromLifeTime(start_horizon, start_incomehorizon, *args, income=start_income, studentloan=start_studentloan, **rate_values, **kwargs) 
    print(start_year, ' ', repr(financials), '\n')  
    
    occupied_horizon = int((occupied_year - start_year) * 12)
    occupied_incomehorizon = start_incomehorizon
    financials = financials.projection(occupied_horizon, occupied_incomehorizon, *args, **rate_values, **kwargs)
    print(occupied_year, ' ', repr(financials), '\n')    
    financials.purchase(int(value), bank=banks['mortgage'])
    print(occupied_year, ' ', repr(financials), '\n')  

    current_horizon = int((current_year - occupied_year) * 12)
    current_incomehorizon = max(int((retirement_year - occupied_year) * 12), 0)
    financials = financials.projection(current_horizon, current_incomehorizon, *args, **rate_values, **kwargs)
    print(current_year, ' ', repr(financials), '\n')  
    
    retirement_horizon = int((retirement_year - current_year) * 12)
    retirement_incomehorizon = max(int((retirement_year - current_year) * 12), 0)    
    financials = financials.projection(retirement_horizon, retirement_incomehorizon, *args, **rate_values, **kwargs)
    print(retirement_year, ' ', repr(financials), '\n')  

    death_horizon = int((death_year - retirement_year) * 12)
    death_incomehorizon = max(int((death_year - retirement_year) * 12), 0)    
    financials = financials.projection(death_horizon, death_incomehorizon, *args, **rate_values, **kwargs)
    print(death_year, ' ', repr(financials), '\n')      
    return financials  
  

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


class Financials(ntuple('Financials', 'income wealth value consumption mortgage studentloan')):
    __stringformat = 'Financials|Assets=${assets:.0f}, Loans=${loans:.0f}, Income=${income:.0f}/MO, Consumption=${consumption:.0f}/MO'
    def __str__(self): 
        content = {**self.flows}
        content.update({'assets':sum([value for value in self.assets.values()])})
        content.update({'loans':sum([value.balance for value in self.loans.values()])})        
        return self.__stringformat.format(**content)     
    
    def __repr__(self): 
        content = {key:str(value) for key, value in self.assets.items()}
        content.update({key:str(value) for key, value in self.flows.items()})
        content.update({key:repr(value) for key, value in self.loans.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 
    
    def __new__(cls, *args, income, wealth, value, consumption, mortgage=None, studentloan=None, **kwargs):        
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        mortgage = mortgage if mortgage is not None else Loan('mortgage', balance=0, rate=0, duration=0, basis='month')
        studentloan = studentloan if studentloan is not None else Loan('studentloan', balance=0, rate=0, duration=0, basis='month')
        return super().__new__(cls, int(income), int(wealth), int(value), int(consumption), mortgage, studentloan)   

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

    def income_projection(self, horizon, incomehorizon, *args, incomerate, **kwargs): 
        assert horizon >= 0 and incomehorizon >= 0
        if horizon >= incomehorizon: return 0
        else: return self.income * projection_factor(incomerate, horizon)
    
    def value_projection(self, horizon, *args, valuerate, **kwargs): 
        assert horizon >= 0
        return self.value * projection_factor(valuerate, horizon)    
    
    def consumption_projection(self, horizon, *args, risktolerance, discountrate, wealthrate, **kwargs):
        assert horizon >= 0
        return self.consumption * projection_factor(theta(discountrate, wealthrate, risktolerance), horizon)    
    
    def mortgage_projection(self, horizon, *args, **kwargs): 
        assert horizon >= 0
        return self.mortgage.projection(horizon)
    
    def studentloan_projection(self, horizon, *args, **kwargs): 
        assert horizon >= 0
        return self.studentloan.projection(horizon)    
    
#    def wealth_projection(self, horizon, incomehorizon, *args, risktolerance, discountrate, wealthrate, incomerate, **kwargs): 
#        assert horizon >= 0 and incomehorizon >= 0
#        w = wealth_factor(wealthrate, horizon)
#        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
#        c = consumption_factor(theta(discountrate, wealthrate, risktolerance), wealthrate, horizon)
#        m = loan_factor(wealthrate, min(horizon, self.mortgage.duration)) if self.mortgage else 0
#        s = loan_factor(wealthrate, min(horizon, self.studentloan.duration)) if self.studentloan else 0
#        return  w * self.wealth + i * self.income - c * self.consumption - m * self.mortgage.payment - s * self.studentloan.payment

    def projection(self, horizon, incomehorizon, *args, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):     
        income = self.income_projection(horizon, incomehorizon, incomerate=incomerate)
        wealth = self.wealth_projection(horizon, incomehorizon, risktolerance=risktolerance, discountrate=discountrate, wealthrate=wealthrate, incomerate=incomerate)
        value = self.value_projection(horizon, valuerate=valuerate)
        consumption = self.consumption_projection(horizon, risktolerance=risktolerance, discountrate=discountrate, wealthrate=wealthrate)
        mortgage = self.mortgage_projection(horizon) 
        studentloan = self.studentloan_projection(horizon)
        return self.__class__(wealth=wealth, value=value, income=income, consumption=consumption, mortgage=mortgage, studentloan=studentloan)

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
        
#    @classmethod
#    def fromLifeTime(cls, horizon, incomehorizon, *args, income, studentloan, wealth=0, terminalwealth=0, risktolerance, discountrate, incomerate, wealthrate, **kwargs):
#        w = wealth_factor(wealthrate, horizon)
#        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
#        c = consumption_factor(theta(discountrate, wealthrate, risktolerance), wealthrate, horizon)
#        x = loan_factor(wealthrate, min(horizon, studentloan.duration))
#        consumption = (w * wealth - terminalwealth + i * income - x * studentloan.payment) / c      
#        return Financials(income=income, wealth=wealth, value=0, consumption=consumption, studentloan=studentloan)    
    










