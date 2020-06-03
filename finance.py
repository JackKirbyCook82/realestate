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

theta = lambda risk, dr, wr: (wr - dr) / risk
wealth_factor = lambda wr, n: farray(1 + wr, n).sum()[()]
income_factor = lambda ir, wr, n: dotarray(farray(1 + ir, n-1), farray(1 + wr, n-1)[::-1])[()]
consumption_factor = lambda cr, wr, n: dotarray(farray(1 + cr, n-1), farray(1 + wr, n-1)[::-1])[()]
loan_factor = lambda wr, n: farray(1 + wr, n-1).sum()[()]    


def createFinancials(geography, date, *args, horizon, age, yearoccupied, education, income, value, rates, ages, banks, educations, broker, **kwargs): 
    start_school = educations[str(education).lower()]
    start_age = int(ages['adulthood'] + (start_school.duration/12))   
    start_year = int(date.year - (int(age) - start_age)) 
    start_income = income / np.prod(np.array([1 + rates['income'](i, units='year') for i in range(start_year, date.year)]))
    start_studentloan = banks['studentloan'].loan(start_school.cost)           
    assert start_age <= int(age) <= ages['death'] 
    assert start_year <= date.year

    purchase_age = int(age) - (date.year - int(yearoccupied))
    purchase_year = int(yearoccupied)  
    purchase_value = value / np.prod(np.array([1 + rates['value'](i, units='year') for i in range(purchase_year,  date.year)]))            
    purchase_downpayment = banks['mortgage'].downpayment(purchase_value)
    purchase_cost = banks['mortgage'].cost(purchase_value - purchase_downpayment)
    purchase_cash = purchase_downpayment + purchase_cost    
    assert start_age <= purchase_age <= int(age) <= ages['death']
    assert start_year <= purchase_year <= date.year 
    
    discountrate = rates['discount'](date.index, units='month')
    wealthrate = rates['wealth'](date.index, units='month')
    valuerate = rates['value'](date.index, units='month')
    incomerate = rates['income'](date.index, units='month')  
    rates = dict(discountrate=discountrate, wealthrate=wealthrate, valuerate=valuerate, incomerate=incomerate)  

    horizon = int((purchase_age - start_age) * 12)
    incomehorizon = int((ages['retirement'] - start_age) * 12)
    assets = dict(income=start_income, wealth=0, value=0)
    loans = dict(studentloan=start_studentloan)
    financials = Financials.fromTerminalWealth(horizon, incomehorizon, *args, terminalwealth=purchase_cash, **assets, **loans, **rates, **kwargs)
    print(repr(financials), '\n')    
    financials = financials.projection(horizon, incomehorizon, *args, **rates, **kwargs)
    print(repr(financials), '\n')
    raise Exception()
    financials = financials.purchase(purchase_value, *args, bank=banks['mortgage'], **kwargs)
    print(repr(financials), '\n')

    horizon = int((int(age) - purchase_age) * 12)
    incomehorizon = int((ages['retirement'] - start_age) * 12)    
    financials = financials.projection(horizon, incomehorizon, *args, **rates, **kwargs)
    print(repr(financials), '\n')
    return financials


class InsufficientFundsError(Exception): 
    def __init__(self, wealth): super().__init__('${} Deficit'.format(int(abs(wealth))))   

class UnstableLifeStyleError(Exception): 
    def __init__(self, consumption): super().__init__('${}/MO Deficit'.format(int(abs(consumption))))
    
class UnsolventLifeStyleError(Exception):
    def __init__(self, wealth): super().__init__('${} Deficit'.format(int(abs(wealth))))   


class Financials(ntuple('Financials', 'income wealth value consumption mortgage studentloan debt')):
    __stringformat = 'Financials|Assets=${assets:.0f}, Debt=${debt:.0f}, Income=${income:.0f}/MO, Consumption=${consumption:.0f}/MO'
    def __str__(self): 
        content = dict(assets=self.wealth + self.value, income=self.income, debt=self.mortgage.balance + self.studentloan.balance + self.debt.balance, consumption=self.consumption)
        return self.__stringformat.format(**content)     
    
    def __repr__(self): 
        content = {'mortgage':repr(self.mortgage), 'studentloan':repr(self.studentloan), 'debt':repr(self.debt)}
        content.update({key:str(value) for key, value in self.todict().items() if key not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()])) 

    def __new__(cls, *args, income, wealth, value, consumption, mortgage=None, studentloan=None, debt=None, **kwargs):            
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        else: consumption = int(consumption)  
        if mortgage is None: mortgage = Loan('mortgage', balance=0, rate=0, duration=0, basis='month')
        if studentloan is None: studentloan = Loan('studentloan', balance=0, rate=0, duration=0, basis='month')
        if debt is None: debt = Loan('debt', balance=0, rate=0, duration=0, basis='month')
        return super().__new__(cls, int(income), int(wealth), int(value), consumption=consumption, mortgage=mortgage, studentloan=studentloan, debt=debt)   

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    @property
    def loans(self): return dict(mortgage=self.mortgage, studentloan=self.studentloan, debt=self.debt)
    @property
    def assets(self): return dict(income=self.income, wealth=self.wealth, value=self.value)

    def income_projection(self, horizon, incomehorizon, *args, risktolerance, incomerate, **kwargs): return self.income * pow(1 + incomerate, min(horizon, incomehorizon))
    def value_projection(self, horizon, *args, risktolerance, valuerate, **kwargs): return self.value * pow(1 + valuerate, horizon)    
    def consumption_projection(self, horizon, *args, risktolerance, discountrate, wealthrate, **kwargs ): return self.consumption * pow(1 + theta(risktolerance, discountrate, wealthrate), horizon)    
    def mortgage_projection(self, horizon, *args, **kwargs): return self.mortgage.projection(horizon)
    def studentloan_projection(self, horizon, *args, **kwargs): return self.studentloan.projection(horizon)
    def debt_projection(self, horizon, *args, **kwargs): return self.debt.projection(horizon)
    def wealth_projection(self, horizon, incomehorizon, *args, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):     
        w = wealth_factor(wealthrate, horizon)
        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizon)
        m = loan_factor(wealthrate, min(horizon, self.mortgage.duration)) if self.mortgage else 0
        s = loan_factor(wealthrate, min(horizon, self.studentloan.duration)) if self.studentloan else 0
        d = loan_factor(wealthrate, min(horizon, self.debt.duration)) if self.debt else 0     
        return  w * self.wealth + i * self.income - c * self.consumption - m * self.mortgage.payment - s * self.studentloan.payment - d * self.debt.payment

    def projection(self, horizon, incomehorizon, *args, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):     
        income = self.income_projection(horizon, incomehorizon, risktolerance=risktolerance, incomerate=incomerate)
        wealth = self.wealth_projection(horizon, incomehorizon, risktolerance=risktolerance, discountrate=discountrate, wealthrate=wealthrate, incomerate=incomerate, valuerate=incomerate)
        if wealth < 0: raise UnsolventLifeStyleError(wealth)   
        value = self.value_projection(horizon, risktolerance=risktolerance, valuerate=valuerate)
        consumption = self.consumption_projection(horizon, risktolerance=risktolerance, discountrate=discountrate, wealthrate=wealthrate)
        mortgage = self.mortgage_projection(horizon) 
        studentloan = self.studentloan_projection(horizon)
        debt = self.debt_projection(horizon)
        assets = dict(income=income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=studentloan, debt=debt)
        return self.__class__(**assets, consumption=consumption, **loans)
 
    def purchase(self, value, *args, bank, **kwargs):
        pass
    
#    def buy(self, value, *args, bank, **kwargs): 
#        assert value > 0 and self.value == 0 and not self.mortgage
#        wealth, mortgage = bank(value, self)
#        if wealth < 0: raise InsufficientFundsError(wealth)  
#        loans = dict(mortgage=mortgage, studentloan=self.studentloan, debt=self.debt)
#        assets = dict(income=self.income, wealth=wealth, value=value)
#        downpayment = bank.downpayment(value)
#        closingcost = bank.cost(value - downpayment)
#        mortgage = bank.loan(value - downpayment)
#        wealth = self.wealth - downpayment - closingcost 
#        coverage = lambda income, payments: income / payments
#        loantovalue = lambda balance, value: balance / value       
#        if not bank.qualify(mortgage.balance, mortgage.payment + self.studentloan.payment + self.debt.payment): 
#            raise InsufficientCoverageError(mortgage.balance, mortgage.payment + self.studentloan.payment + self.debt.payment)                
    
    def sale(self, *args, broker, **kwargs):
        pass
    
#    def sale(self, *args, broker, **kwargs): 
#        proceeds = self.value - broker.cost(self.value) - self.mortgage.balance 
#        loans = dict(mortgage=self.mortgage.payoff(), studentloan=self.studentloan, debt=self.debt)
#        assets = dict(income=self.income, wealth=self.wealth + proceeds, value=0)
#        newfinancials = self.__class__(*args, **assets, **loans, **kwargs)  
#        return newfinancials
    
    @classmethod 
    def fromConsumption(cls, horizon, incomehorizon, *args, consumption, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):            
        income, wealth, value = [int(kwargs[asset]) for asset in ('income', 'wealth', 'value',)]
        mortgage, studentloan, debt = [kwargs.get(loan, None) for loan in ('mortgage', 'studentloan', 'debt',)]            
        w = wealth_factor(wealthrate, horizon)
        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizon)
        m, mpayment = (loan_factor(wealthrate, min(horizon, mortgage.duration)), mortgage.payment,) if mortgage else (0, 0,)
        s, spayment = (loan_factor(wealthrate, min(horizon, studentloan.duration)), studentloan.payment,) if studentloan else (0, 0,)
        d, dpayment = (loan_factor(wealthrate, min(horizon, debt.duration)), debt.payment,) if debt else (0, 0,)    
        terminalwealth = w * wealth + i * income - c * consumption - m * mpayment - s * spayment - d * dpayment
        if terminalwealth < 0: raise UnsolventLifeStyleError(terminalwealth)  
        assets = dict(income=income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=studentloan, debt=debt)
        return cls(consumption=consumption, **assets, **loans)

    @classmethod
    def fromTerminalWealth(cls, horizon, incomehorizon, *args, terminalwealth, risktolerance, discountrate, wealthrate, incomerate, valuerate, **kwargs):   
        income, wealth, value = [int(kwargs[asset]) for asset in ('income', 'wealth', 'value',)]
        mortgage, studentloan, debt = [kwargs.get(loan, None) for loan in ('mortgage', 'studentloan', 'debt',)]            
        w = wealth_factor(wealthrate, horizon)
        i = income_factor(incomerate, wealthrate, min(horizon, incomehorizon))
        c = consumption_factor(theta(risktolerance, discountrate, wealthrate), wealthrate, horizon)
        m, mpayment = (loan_factor(wealthrate, min(horizon, mortgage.duration)), mortgage.payment,) if mortgage else (0, 0,)
        s, spayment = (loan_factor(wealthrate, min(horizon, studentloan.duration)), studentloan.payment,) if studentloan else (0, 0,)
        d, dpayment = (loan_factor(wealthrate, min(horizon, debt.duration)), debt.payment,) if debt else (0, 0,)     
        consumption = (w * wealth - terminalwealth + i * income - m * mpayment - s * spayment - d * dpayment) / c
        if consumption < 0: raise UnstableLifeStyleError(consumption)  
        else: consumption =  int(consumption)    
        assets = dict(income=income, wealth=wealth, value=value)
        loans = dict(mortgage=mortgage, studentloan=studentloan, debt=debt)
        return cls(consumption=consumption, **assets, **loans)




if __name__ == "__main__":
    from variables import Geography, Date
    from realestate.economy import Bank, Education, Broker, Rate
    
    AGES = {'adulthood':15, 'retirement':65, 'death':95} 
    RISKTOLERANCE = 2
    HORIZON = 20
    
    age = 35 
    yearoccupied = 2010
    education = 'Graduate'
    
    geography =Geography.fromstr('state=6|county=29|tract=*')
    date = Date.fromstr('2018')
    
    mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
    studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
    debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')
        
    basic = Education('basic', cost=0, duration=0, basis='year')
    grade = Education('grade', cost=0, duration=3, basis='year')
    associates = Education('associates', cost=25000, duration=5, basis='year')
    bachelors = Education('bachelors', cost=50000, duration=7, basis='year')
    graduate = Education('gradudate', cost=75000, duration=10, basis='year')
    
    broker = Broker(commissions=0.03)
    educations = {'uneducated':basic, 'gradeschool':grade, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
    banks = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}
    
    assets = dict(income=int(50000/12), 
                  value=150000)
    rates = dict(wealth=Rate(date.index, 0.03, basis='year'), 
                 discount=Rate(date.index, 0.01, basis='year'), 
                 income=Rate(date.index, 0.035, basis='year'), 
                 value=Rate(date.index, 0.05, basis='year'))

    x = createFinancials(geography, date, horizon=HORIZON, age=age, yearoccupied=yearoccupied, education=education, risktolerance=RISKTOLERANCE, 
                         rates=rates, ages=AGES, **assets, educations=educations, banks=banks, broker=broker)

 









