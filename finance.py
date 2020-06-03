# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Finance Objects
@author: Jack Kirby Cook

"""

import numpy as np
from collections import namedtuple as ntuple

#from utilities.dispatchers import key_singledispatcher as keydispatcher

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

theta = lambda risk, dr, wr: (wr - dr) / risk
wealth_factor = lambda wr, n: farray(1 + wr, n).sum()[()]
income_factor = lambda ir, wr, n: dotarray(farray(1 + ir, n-1), farray(1 + wr, n-1)[::-1])[()]
consumption_factor = lambda cr, wr, n: dotarray(farray(1 + cr, n-1), farray(1 + wr, n-1)[::-1])[()]
loan_factor = lambda wr, n: farray(1 + wr, n-1).sum()[()]    


def createFinancials(geography, date, *args, horizon, age, yearoccupied, education, income, value, rates, ages, banks, educations, broker, **kwargs): 
    discountrate = rates['discount'](date.index, units='month')
    wealthrate = rates['wealth'](date.index, units='month')
    valuerate = rates['value'](date.index, units='month')
    incomerate = rates['income'](date.index, units='month')  
    rates = dict(discountrate=discountrate, wealthrate=wealthrate, valuerate=valuerate, incomerate=incomerate)      
    
#    start_school = educations[str(education).lower()]
#    start_age = int(ages['adulthood'] + (start_school.duration/12))   
#    start_year = int(date.year - (int(age) - start_age)) 
#    start_income = income / np.prod(np.array([1 + rates['income'](i, units='year') for i in range(start_year, date.year)]))
#    start_studentloan = banks['studentloan'].loan(start_school.cost)           
#    assert start_age <= int(age) <= ages['death'] 
#    assert start_year <= date.year
#
#    purchase_age = int(age) - (date.year - int(yearoccupied))
#    purchase_year = int(yearoccupied)  
#    purchase_value = value / np.prod(np.array([1 + rates['value'](i, units='year') for i in range(purchase_year,  date.year)]))            
#    purchase_downpayment = banks['mortgage'].downpayment(purchase_value)
#    purchase_cost = banks['mortgage'].cost(purchase_value - purchase_downpayment)
#    purchase_cash = purchase_downpayment + purchase_cost    
#    assert start_age <= purchase_age <= int(age) <= ages['death']
#    assert start_year <= purchase_year <= date.year 
#    
#    horizon = int((purchase_age - start_age) * 12)
#    incomehorizon = int((ages['retirement'] - start_age) * 12)
#    assets = dict(income=start_income, wealth=0, value=0)
#    loans = dict(studentloan=start_studentloan)
#    financials = Financials.fromTerminalWealth(horizon, incomehorizon, *args, terminalwealth=purchase_cash, **assets, **loans, **rates, **kwargs) 
#    financials = financials.projection(horizon, incomehorizon, *args, **rates, **kwargs)
#    
#    horizon = int((int(age) - purchase_age) * 12)
#    incomehorizon = int((ages['retirement'] - start_age) * 12)      
#    financials = financials.purchase(horizon, incomehorizon, *args, value=purchase_value, terminalwealth=0, bank=banks['mortgage'], **rates, **kwargs)
#    return financials


#@keydispatcher
#def terminal_wealth(strategy, horizon, *args, **kwargs): raise KeyError(strategy)
#@terminal_wealth.register('ponzi')
#def terminal_wealth_ponzi(horizon, *args, **kwargs):
#    pass
#@terminal_wealth.register('survive')
#def terminal_wealth_survive(horizon, *args, **kwargs):
#    return 0
#@terminal_wealth.register('maintain')
#def terminal_wealth_maintain(horizon, *args, wealth, **kwargs):
#    return wealth
#@terminal_wealth.register('target')
#def terminal_wealth_target(horizon, *args, targetwealth, **kwargs):
#    return targetwealth
#@terminal_wealth.register('retirement')
#def terminal_wealth_retirement(horizon, *args, value, mortgage, studentloan, debt, valuerate, **kwargs):
#    return mortgage.projection(horizon) + studentloan.projection(horizon) + debt.projection(horizon) - (value * pow(1 + valuerate, horizon))    
#@terminal_wealth.register('bequest')
#def terminal_wealth_bequest(horizon, *args, bequest, value, mortgage, studentloan, debt, valuerate, **kwargs):
#    return mortgage.projection(horizon) + studentloan.projection(horizon) + debt.projection(horizon) - (value * pow(1 + valuerate, horizon)) - bequest   
    
    
class InsufficientFundsError(Exception): 
    @property
    def deficit(self): return self.__deficit
    def __init__(self, wealth_deficit): self.__deficit = int(abs(wealth_deficit))
    def __str__(self): return super().__str__('${}'.format(self.deficit))

class UnsolventLifeStyleError(Exception): 
    @property
    def deficit(self): return self.__deficit
    def __init__(self, wealth_deficit): self.__deficit = int(abs(wealth_deficit))
    def __str__(self): return super().__str__('${}'.format(self.deficit))

class UnstableLifeStyleError(Exception): 
    @property
    def deficit(self): return self.__deficit
    def __init__(self, consumption_deficit): self.__deficit = int(abs(consumption_deficit))
    def __str__(self): return super().__str__('${}/MO'.format(self.deficit))    
    
class InsufficientCoverageError(Exception):
    @property
    def coverage(self): return self.__coverage
    @property
    def requiredcoverage(self): return self.__requiredcoverage
    def __init__(self, coverage, requiredcoverage): self.__coverage, self.__requiredcoverage = coverage, requiredcoverage
    def __str__(self): return super().__str__('{:.2f} < {:.2f}'.format(self.coverage, self.requiredcoverage)) 
    

class Financials(ntuple('Financials', 'income wealth value consumption mortgage studentloan debt credit')):
    __stringformat = 'Financials|Assets=${assets:.0f}, Loans=${debt:.0f}, Income=${income:.0f}/MO, Consumption=${consumption:.0f}/MO'
    def __str__(self): 
        content = dict(assets=self.wealth + self.value, income=self.income, loans=sum([loan.balance for loan in self.loans.values()]))
        return self.__stringformat.format(**content)     
    
    def __repr__(self): 
        content = {key:repr(value) for key, value in self.loans.items()}
        content.update({key:str(value) for key, value in self.todict().items() if key not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 

    def __new__(cls, *args, income, wealth, value, consumption, **kwargs):        
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        else: consumption = int(consumption)  
        loans = {loankey:kwargs.get(loankey, None) for loankey in ('mortgage' 'studentloan', 'debt', 'credit',)}
        loans = {key:(Loan(key, balance=0, rate=0, duration=0, basis='month') if value is None else value) for key, value in loans.items()}
        return super().__new__(cls, int(income), int(wealth), int(value), consumption=consumption, **loans)   

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    @property
    def loans(self): return dict(mortgage=self.mortgage, studentloan=self.studentloan, debt=self.debt, credit=self.credit)
    @property
    def assets(self): return dict(income=self.income, wealth=self.wealth, value=self.value)

    def income_projection(self, horizon, incomehorizon, *args, risktolerance, incomerate, **kwargs): return self.income * pow(1 + incomerate, min(horizon, incomehorizon))
    def value_projection(self, horizon, *args, risktolerance, valuerate, **kwargs): return self.value * pow(1 + valuerate, horizon)    
    def consumption_projection(self, horizon, *args, risktolerance, discountrate, wealthrate, **kwargs ): return self.consumption * pow(1 + theta(risktolerance, discountrate, wealthrate), horizon)    
    def mortgage_projection(self, horizon, *args, **kwargs): return self.mortgage.projection(horizon)
    def studentloan_projection(self, horizon, *args, **kwargs): return self.studentloan.projection(horizon)    
    def debt_projection(self, horizon, *args, **kwargs): return self.debt.projection(horizon)
    def credit_projection(self, horizon, *args, **kwargs): return self.credit.projection(horizon)
    def wealth_projection(self, horizon, incomehorizon, *args, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):     
        w = wealth_factor(wealthrate, horizon)
        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizon)
        m = loan_factor(wealthrate, min(horizon, self.mortgage.duration)) if self.mortgage else 0
        s = loan_factor(wealthrate, min(horizon, self.studentloan.duration)) if self.studentloan else 0
        d = loan_factor(wealthrate, min(horizon, self.debt.duration)) if self.debt else 0     
        x = loan_factor(wealthrate, min(horizon, self.credit.duration)) if self.credit else 0   
        return  w * self.wealth + i * self.income - c * self.consumption - m * self.mortgage.payment - s * self.studentloan.payment - d * self.debt.payment - x * self.credit.payment

    def projection(self, horizon, incomehorizon, *args, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):     
        income = self.income_projection(horizon, incomehorizon, risktolerance=risktolerance, incomerate=incomerate)
        wealth = self.wealth_projection(horizon, incomehorizon, risktolerance=risktolerance, discountrate=discountrate, wealthrate=wealthrate, incomerate=incomerate, valuerate=incomerate)
        value = self.value_projection(horizon, risktolerance=risktolerance, valuerate=valuerate)
        consumption = self.consumption_projection(horizon, risktolerance=risktolerance, discountrate=discountrate, wealthrate=wealthrate)
        mortgage = self.mortgage_projection(horizon) 
        studentloan = self.studentloan_projection(horizon)
        credit = self.credit_projection(horizon)
        debt = self.debt_projection(horizon)
        assets = dict(income=income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=studentloan, debt=debt, credit=credit)
        return self.__class__(**assets, consumption=consumption, **loans)
 
    def purchase(self, horizon, incomehorizon, *args, value, bank, **kwargs):
        assert value > 0 and self.value == 0 and not self.mortgage
        downpayment = bank.downpayment(value)
        closingcost = bank.cost(value - downpayment)
        wealth = self.wealth - downpayment - closingcost
        if wealth < 0: raise InsufficientFundsError(wealth)       
        mortgage = bank.loan(value - downpayment)        
        coverage = self.income / sum([loan.payment for loan in self.loans.values()])
        if coverage < bank.coverage: raise InsufficientCoverageError(coverage, bank.coverage)
        assets = dict(income=self.income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=self.studentloan, debt=self.debt, credit=self.credit)
        return self.fromTerminalWealth(horizon, incomehorizon, *args, **assets, **loans, **kwargs)
        
    def sale(self, horizon, incomehorizon, *args, broker, **kwargs):
        proceeds = self.value - broker.cost(self.value) - self.mortgage.balance 
        loans = dict(mortgage=self.mortgage.payoff(), studentloan=self.studentloan, debt=self.debt, credit=self.credit)
        assets = dict(income=self.income, wealth=self.wealth + proceeds, value=0)
        return self.fromTerminalWealth(horizon, incomehorizon, *args, **assets, **loans, **kwargs)  

    @classmethod 
    def fromConsumption(cls, horizon, incomehorizon, *args, consumption, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):      
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        else: consumption =  int(consumption)           
        income, wealth, value = [int(kwargs[asset]) for asset in ('income', 'wealth', 'value',)]
        mortgage, studentloan, debt, credit = [kwargs.get(loan, None) for loan in ('mortgage', 'studentloan', 'debt', 'credit',)]            
        w = wealth_factor(wealthrate, horizon)
        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizon)
        m, mpayment = (loan_factor(wealthrate, min(horizon, mortgage.duration)), mortgage.payment,) if mortgage else (0, 0,)
        s, spayment = (loan_factor(wealthrate, min(horizon, studentloan.duration)), studentloan.payment,) if studentloan else (0, 0,)
        d, dpayment = (loan_factor(wealthrate, min(horizon, debt.duration)), debt.payment,) if debt else (0, 0,)    
        x, xpayment = (loan_factor(wealthrate, min(horizon, credit.duration)), credit.payment,) if credit else (0, 0,)   
        assets = dict(income=income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=studentloan, debt=debt, credit=credit)
        terminalwealth = w * wealth + i * income - c * consumption - m * mpayment - s * spayment - d * dpayment - x * xpayment
        if terminalwealth < 0: raise UnsolventLifeStyleError(terminalwealth)  
        return cls(**assets, consumption=consumption, **loans)

    @classmethod
    def fromTerminalWealth(cls, horizon, incomehorizon, *args, terminalwealth, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):   
        if terminalwealth < 0: raise UnsolventLifeStyleError(terminalwealth)  
        income, wealth, value = [int(kwargs[asset]) for asset in ('income', 'wealth', 'value',)]
        mortgage, studentloan, debt, credit = [kwargs.get(loan, None) for loan in ('mortgage', 'studentloan', 'debt', 'credit',)]            
        w = wealth_factor(wealthrate, horizon)
        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizon)
        m, mpayment = (loan_factor(wealthrate, min(horizon, mortgage.duration)), mortgage.payment,) if mortgage else (0, 0,)
        s, spayment = (loan_factor(wealthrate, min(horizon, studentloan.duration)), studentloan.payment,) if studentloan else (0, 0,)
        d, dpayment = (loan_factor(wealthrate, min(horizon, debt.duration)), debt.payment,) if debt else (0, 0,)     
        x, xpayment = (loan_factor(wealthrate, min(horizon, credit.duration)), credit.payment,) if credit else (0, 0,)   
        assets = dict(income=income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=studentloan, debt=debt, credit=credit)
        consumption = (w * wealth - terminalwealth + i * income - m * mpayment - s * spayment - d * dpayment  - x * xpayment) / c
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        else: consumption =  int(consumption)    
        return cls(**assets, consumption=consumption, **loans)













