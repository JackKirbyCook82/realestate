# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from collections import namedtuple as ntuple

from realestate.economy import Loan

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Financials']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


theta = lambda dr, wr, risk: (wr - dr) / risk
pad = lambda *xns: max([len(xn) for xn in xns])

loanvalue = lambda x, r, n, i: np.fv(r, i, -np.pmt(r, n, x), -x)
flowvalue = lambda x, r, i: np.fv(r, i, 0, -x)
assetvalue = lambda x, r, i: np.fv(r, i, 0, -x)

iarray = lambda n: np.arange(n+1)
farray = lambda r, n: (np.ones(n) * np.array(1 + r)) ** iarray(n-1) 

imatrix = lambda n: np.triu(-np.subtract(*np.mgrid[0:n, 0:n]))
rmatrix = lambda r, n: np.ones((n,n)) * (1+r)
fmatrix = lambda r, n: np.triu(rmatrix(r, n) ** imatrix(n))

loanarray = lambda x, r, n: np.fv(r, iarray(n), -np.pmt(r, n, x), -x)
flowarray = lambda x, r, n: np.fv(r, iarray(n), 0, -x)
assetarray = lambda x, r, n: np.fv(r, iarray(n), 0, -x)
payarray = lambda x, r, n: np.concatenate([np.array([0]), -np.ones(n) * np.pmt(r, n, x)])
investarray = lambda xn, r: np.sum(fmatrix(r, len(xn)) * np.expand_dims(xn, 1), axis=0)

addarrays = lambda *xns: sum(xns)
padarrays = lambda *xns: [np.pad(xn, (0, max(pad(*xns)-len(xn), 0)), mode='constant') for xn in xns]

wealth_factor = lambda wr, n: np.array(1 + wr) ** n
income_factor = lambda ir, wr, n: np.sum(farray(ir, n) * farray(wr, n))
consumption_factor = lambda cr, wr, n: np.sum(farray(cr, n) * farray(wr, n)) 
loan_factor = lambda wr, n: np.sum(farray(wr, n))


class UnsolventLifeStyleError(Exception): 
    @property
    def wealth(self): return self.__wealth
    def __str__(self): return '${}'.format(self.wealth)
    def __init__(self, wealth): 
        assert wealth < 0
        self.__wealth = int(abs(wealth))
        super().__init__()
    
class UnstableLifeStyleError(Exception): 
    @property
    def consumption(self): return self.__consumption
    def __str__(self): return '-${}/MO'.format(self.deficit)    
    def __init__(self, consumption): 
        assert consumption < 0
        self.__consumption = int(abs(consumption))
        super().__init__()

class InsufficientFundsError(Exception): 
    @property
    def wealth(self): return self.__wealth
    def __str__(self): return '${}'.format(self.wealth)
    def __init__(self, wealth): 
        assert wealth < 0
        self.__wealth = int(abs(wealth))
        super().__init__()

class InsufficientCoverageError(Exception):
    @property
    def coverage(self): return self.__coverage
    @property
    def required(self): return self.__required
    def __str__(self): return '{:.2f} < {:.2f}'.format(self.coverage, self.__required)
    def __init__(self, coverage, required): 
        self.__coverage, self.__required = coverage, required
        super().__init__()


def createFinancialsKey(*args, incomehorizon, consumptionhorizon, income, consumption, wealth, value, mortgage, studentloan, **kwargs):
    mortgage_key, studentloan_key = [loan.key for loan in (mortgage, studentloan)]    
    return (incomehorizon, consumptionhorizon, int(income), int(consumption), int(wealth), int(value), hash(mortgage_key), hash(studentloan_key),)
        

class Financials(ntuple('Financials', 'incomehorizon consumptionhorizon income wealth value consumption mortgage studentloan')):
    __stringformat = 'Financials({horizon})|Assets=${assets:.0f}, Loans=${loans:.0f}, Income=${income:.0f}/MO, Consumption=${consumption:.0f}/MO'
    def __str__(self): 
        content = {**self.flows, 'horizon':self.consumptionhorizon}
        content.update({'assets':sum([value for value in self.assets.values()])})
        content.update({'loans':sum([value.balance for value in self.loans.values()])})        
        return self.__stringformat.format(**content)     
    
    def __repr__(self): 
        content = {'incomehorizon':str(self.incomehorizon), 'consumptionhorizon':str(self.consumptionhorizon)}
        content.update({key:str(round(value, ndigits=1)) for key, value in self.assets.items()})
        content.update({key:str(round(value, ndigits=1)) for key, value in self.flows.items()})
        content.update({key:repr(value) for key, value in self.loans.items() })
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 
    
    def __new__(cls, income_horizon , consumption_horizon, *args, income, wealth, value, consumption, mortgage=None, studentloan=None, **kwargs):        
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        mortgage = mortgage if mortgage else Loan('mortgage', balance=0, basis='month')
        studentloan = studentloan if studentloan else Loan('studentloan', balance=0, basis='month')
        return super().__new__(cls, int(income_horizon), int(consumption_horizon), income, wealth, value, consumption, mortgage, studentloan)   

    def __init__(self, *args, date, discountrate, risktolerance, **kwargs):
        try: year = date.year
        except: year = int(date)
        try: self.__discountrate = discountrate(year, units='month')
        except TypeError: self.__discountrate
        self.__risktolerance = risktolerance

    @property
    def key(self): return hash(createFinancialsKey(**self.todict()))
    def __ne__(self, other): return not self.__eq__()
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return self.key == other.key
    
    @property
    def discountrate(self): return self.__discountrate
    @property
    def risktolerance(self): return self.__risktolerance
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

    def projection(self, *args, discountrate, wealthrate, valuerate, incomerate, **kwargs):       
        mortgage = loanarray(self.mortgage.balance, self.mortgage.rate, self.mortgage.duration) if self.mortgage else np.array([])
        studentloan = loanarray(self.studentloan.balance, self.studentloan.rate, self.studentloan.duration) if self.studentloan else np.array([])
        income = flowarray(self.income, incomerate, self.incomehorizon)
        consumption = flowarray(self.consumption, theta(discountrate, wealthrate, self.risktolerance), self.consumptionhorizon)
        value = assetarray(self.value, valuerate, self.consumptionhorizon)
        mortgagepayments = payarray(self.mortgage.balance, self.mortgage.rate, self.mortgage.duration) if self.mortgage else np.array([])
        studentloanpayments = payarray(self.studentloan.balance, self.studentloan.rate, self.studentloan.duration) if self.studentloan else np.array([])       
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

    def __call__(self, horizon, *args, wealthrate, valuerate, incomerate, **kwargs):
        assert isinstance(horizon, int) and horizon <= self.consumptionhorizon
        income = flowvalue(self.income, incomerate, min(horizon, self.incomehorizon)) if horizon <= self.incomehorizon else 0
        consumption = flowvalue(self.consumption, theta(self.discountrate, wealthrate, self.risktolerance), horizon) 
        mortgage = self.mortgage(horizon) if self.mortgage else None
        studentloan = self.studentloan(horizon) if self.studentloan else None
        value = assetvalue(self.value, valuerate, horizon) 
        incomearray = flowarray(self.income, incomerate, self.incomehorizon)
        consumptionarray = flowarray(self.consumption, theta(self.discountrate, wealthrate, self.risktolerance), self.consumptionhorizon)
        mortgagepayments = payarray(self.mortgage.balance, self.mortgage.rate, self.mortgage.duration) if self.mortgage else np.array([])
        studentloanpayments = payarray(self.studentloan.balance, self.studentloan.rate, self.studentloan.duration) if self.studentloan else np.array([])        
        incomearray, consumptionarray, mortgagepayments, studentloanpayments = padarrays(incomearray, consumptionarray, mortgagepayments, studentloanpayments)
        savings = addarrays(incomearray, -consumptionarray, -mortgagepayments, -studentloanpayments)       
        cashflows = np.concatenate([np.array([self.wealth]), savings])
        wealth = investarray(cashflows, wealthrate)[horizon]
        consumptionhorizon = self.consumptionhorizon - horizon 
        incomehorizon = max(self.incomehorizon - horizon, 0)
        assets = dict(wealth=wealth, value=value)
        flows = dict(income=income, consumption=consumption)
        loans = dict(mortgage=mortgage, studentloan=studentloan)
        return self.__class__(incomehorizon, consumptionhorizon, **assets, **flows, **loans)
        
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
        payments = sum([loan.payment for loan in self.loans.values() if loan])
        coverage = self.income / payments        
        if wealth < 0: raise InsufficientFundsError(wealth)       
        if coverage < bank.coverage: raise InsufficientCoverageError(coverage, bank.coverage)
        assets = dict(wealth=wealth, value=value)
        flows = dict(income=self.income, consumption=self.consumption)
        loans = dict(mortgage=mortgage, studentloan=self.studentloan)
        return self.__class__(self.incomehorizon, self.consumptionhorizon, **assets, **flows, **loans)

    @classmethod
    def create(cls, *args, income, savings, wealth=0, value=0, **kwargs):
        assert 0 <= savings <= 1
        return cls(*args, income=int(income/12), consumption=int(income*(1-savings)/12), wealth=wealth, value=value, **kwargs)
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    





