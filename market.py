# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


class NamedTupleMethods(object):
    def __getitem__(self, key): return self.todict()[key]  
    def keys(self): return list(self.todict().keys())
    def values(self): return list(self.todict().values())
    def items(self): return zip(self.keys(), self.values())
    def todict(self): return self._asdict()    


def income_ratio_integral(duration, income_rate, wealth_rate):
    income_factor = income_rate - wealth_rate
    return (1 - pow((1 + income_factor), duration)) / income_factor

def loan_ratio_integral(duration, loan_rate, wealth_rate):
    loan_factor = (1 + loan_rate)
    wealth_factor = (1 - wealth_rate)
    return (loan_rate / wealth_rate) * ((pow(wealth_factor, duration) - 1) / (pow(loan_factor, duration) - 1)) * pow(loan_factor, duration)

def consumption_ratio_integral(duration, discount_rate, risk_rate, wealth_rate):
    theda = (wealth_rate - discount_rate) / risk_rate
    consumption_factor = theda - wealth_rate
    return (1 - pow((1 + consumption_factor), duration)) / consumption_factor


Housing_Sgmts = ntuple('Housing', 'crime school space community proximity quality')
class Housing(Housing_Sgmts, NamedTupleMethods):  
    pass


Rate_Sgmts = ntuple('Rates', 'discount risk wealth value income mortgage studentloan debt')
class Rates(Rate_Sgmts, NamedTupleMethods): 
    pass
    

Duration_Sgmts = ntuple('Durations', 'child working retired mortgage studentloan debt')
class Durations(Duration_Sgmts):
    def labor(self, current): return max(0, self.child + self.working - current)
    def life(self, current): return max(0, self.child + self.working + self.retired - current)
    def payoff(self, loan, current): return max(0, getattr(self, loan) - current)
        

Household_Financials_Sgmts = ntuple('Household_Financials', 'income value wealth mortgage studentloan debt')
class Household_Financials(Household_Financials_Sgmts):
    def __new__(cls, *args, **kwargs):        
        return super().__new__(cls, **{kwargs[field] for field in cls._fields})

    #@property
    #def consumption(self): return self.__consumption
    #def __init__(self, *args, current, target_horizon, target_wealth, rates, durations, **kwargs):
    #    income_integral = income_ratio_integral(min(durations.labor(current), target_horizon), rates.income, rates.wealth) * self.income       
    #    
    #    mortgage_integral = loan_ratio_integral(min(durations.payoff('mortgage', target_horizon)), rates.mortgage, rates.wealth) * self.mortgage
    #    studentloan_integral = loan_ratio_integral(min(durations.payoff('studentloan', target_horizon)), rates.studentloan, rates.wealth) * self.studentloan
    #    debt_integral = loan_ratio_integral(min(durations.payoff('debt', target_horizon)), rates.debt, rates.wealth) * self.debt
    #    
    #    wealth_integral = self.wealth - (target_wealth / pow((1 + rates.wealth), target_horizon))
    #    consumption_integral = consumption_ratio_integral(min(durations.life(current), target_horizon), rates.discount, rates.risk, rates.wealth)
    #    
    #    residual_integral = wealth_integral + income_integral - mortgage_integral - studentloan_integral - debt_integral
    #    self.__consumption = consumption_integral / residual_integral
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        