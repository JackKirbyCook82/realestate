# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Rates', 'Durations', 'Economy', 'Loan', 'Financials', 'Housing', 'Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


ADULTHOOD = 15
RETIREMENT = 65
DEATH = 95

_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


class Rates(ntuple('Rates', 'discount wealth value income mortgage studentloan debt')): 
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    
    
    def __repr__(self): return '{}(discount={}, wealth={}, value={}, income={}, mortgage={}, studentloan={}, debt={})'.format(self.__class__.__name__, *self._fields)
    def __new__(cls, basis, *args, **kwargs): 
        if basis == 'year': function = lambda rate: pow(rate + 1, 1/12) - 1
        elif basis == 'month': function = lambda rate: rate
        else: raise ValueError(basis)
        return super().__new__(cls, *[float(function(rate)) for rate in cls._fields])
    
    
    def theta(self, risk): return (self.wealth - self.discount) / risk    
    def income_integral(self, horizon): return (1 - pow(1 + self.income - self.wealth, horizon)) / (self.income - self.wealth)
    def consumption_integal(self, horizon, risk): return (1 - pow(1 + self.theta(risk) - self.wealth, horizon)) / (self.theta(risk) - self.wealth)
    
    def mortgage_integral(self, horizon): return self.loan_integral(self, 'mortgage', horizon) 
    def studentloan_integral(self, horizon): return self.loan_integral(self, 'studentloan', horizon) 
    def debt_integal(self, horizon): return self.loan_integral(self, 'debt', horizon) 
    
    def loan_integral(self, loan, horizon): return self.__loanfactor(loan) * (pow(1 - self.wealth, horizon) - 1) / self.wealth
    def __loanfactor(self, loan, horizon): return (getattr(self, loan) * pow(1 + getattr(self, loan), horizon)) / (pow(1 + getattr(self, loan), horizon) - 1)


class Durations(ntuple('Duration', 'mortgage studentloan debt')):
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    
    
    def __repr__(self): return '{}(mortgage={}, studentloan={}, debt={})'.format(self.__class__.__name__, *self._fields)
    def __new__(cls, basis, *args, **kwargs): 
        if basis == 'year': function = lambda rate: rate * 12
        elif basis == 'month': function = lambda rate: rate
        else: raise ValueError(basis)        
        return super().__new__(cls, *[int(function(rate)) for rate in cls._fields])
 

class Economy(ntuple('Economy', 'rates durations risk price commisions financing coverage loantovalue')):
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    
    
    def __repr__(self): 
        fmt = '{}(rates={}, durations={}, price={}, commisions={}, financing={}, coverage={}, loantovalue={})' 
        return fmt.format(self.__class__.__name__, repr(self.rates), repr(self.durations), *self._fields[1:])
    def __new__(cls, *args, rates, durations, **kwargs):
        assert isinstance(rates, Rates)
        assert isinstance(rates, Durations)
        return super().__new__(cls, rates, durations, *[field for field in cls._fields])


class Loan(ntuple('Loan', 'name balance rate duration')):
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()    

    def __repr__(self): return '{}(name={}, balance={}, rate={}, duration={})'.format(self.__class__.__name__, *self._fields)
    def __str__(self): return '{name} | ${balance} for {duration} PERS @ {rate} %/PER'.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict()})

    @property
    def factor(self): return 1 + self.rate
    @property
    def payment(self): return (self.balance * self.rate * pow(self.factor, self.duration))/(pow(self.factor, self.duration) - 1)
    @property
    def interest(self): return self.balance * self.rate
    @property
    def principal(self): return self.payment - self.interest
    
    def __call__(self, duration): 
        duration = min(duration, self.duration)
        newbalance = self.balance * (pow(self.factor, duration) - pow(self.factor, self.duration)) / (pow(self.factor, duration) - 1)
        return self.__class__(min(newbalance, 0), self.rate, self.duration - duration)


class InsufficientFundsError(Exception):
    def __init__(self, financials): super().__init__('available={}, required={}'.format(financials.wealth, 0))

class InsufficientCoverageError(Exception):
    def __init__(self, financials, coverage): super().__init__('available={}, required={}'.format(financials.coverage, coverage))

class UnstableLifeStyleError(Exception):
    def __init__(self, consumption): super().__init__('available={}, required={}'.format(consumption, 0))


class Financials(ntuple('Financials', 'wealth income value mortgage studentloan debt')):
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()
    
    @property
    def coverage(self): return self.income / (self.mortgage.payment + self.studentloan.payment + self.debt.payment)
    @property
    def loantovalue(self): return self.mortgage / self.value

    def __new__(cls, *args, wealth, income, value, mortgage, studentloan, debt, **kwargs):        
        if mortgage is None: mortgage = Loan('mortgage', 0, 0, 0) 
        if studentloan is None: studentloan = Loan('studentloan', 0, 0, 0)
        if debt is None: debt = Loan('debt', 0, 0, 0)
        assert all([isinstance(loan, Loan) for loan in (mortgage, studentloan, debt)])
        return super().__new__(cls, wealth, income, value, mortgage, studentloan, debt)

    def __proceeds(self, commisions): return self.value * (1 - commisions) - self.mortgage.balance 
    def __commisions(self, value, commisions): return value * (1 + commisions)
    def __financing(self, value, financing): return value * (1 + financing)
    def __downpayment(self, value, loantovalue): return value * (1 - loantovalue)
    
    def sale(self, *args, economy, **kwargs): return self.__class__(self.wealth + self.__proceeds(economy.commisions), self.income, 0, None, self.studentloan, self.debt)
    def buy(self, value, *args, economy, **kwargs): 
        closingcost = self.__commisions(value, economy.commisions, economy.financing)
        downpayment = self.__downpayment(value, economy.loantovalue)
        mortgage = Loan('mortgage', value - downpayment, economy.rates.mortgage, economy.durations.mortgage)
        newfinancials = self.__class__(self.wealth - downpayment - closingcost, self.income, value, mortgage, self.studentloan, self.debt)
        if newfinancials.wealth < 0: raise InsufficientFundsError(newfinancials)  
        if newfinancials.coverage < economy.coverage: raise InsufficientCoverageError(newfinancials, economy.coverage)
        return newfinancials
          
    def __call__(self, household, *args, economy, **kwargs): 
        w = self.wealth - (household.horizonwealth / pow(1 + economy.rates.wealth, household.horizon)) 
        i = economy.rates.income_integral(min(household.horizon, household.retirement))
        c = economy.rates.consumption_integal(household.horizon, economy.risk)
        m = economy.rates.mortgage_integral(min(household.horizon, self.mortgage.duration))
        s = economy.rates.studentloan_integral(min(household.horizon, self.studentloan.duration))
        d = economy.rates.debt_integal(min(household.horizon, self.debt.duration))        
        consumption = (w + (i * self.income) - (m * self.mortgage.balance) - (s * self.studentloan.balance) - (d * self.debt.balance)) / c
        if consumption < 0: raise UnstableLifeStyleError(consumption)
        return consumption
       
        
class PrematureHouseholderError(Exception):
    def __init__(self, age): super().__init__('{} < {}'.format(age, ADULTHOOD))
    
class DeceasedHouseholderError(Exception):
    def __init__(self, age): super().__init__('{} > {}'.format(age, DEATH))
    

class Household(ntuple('Household', 'age race origin language english education children size')):
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()
    
    @property
    def period(self): return int((self.currentage * 12) - (ADULTHOOD * 12))
    @property
    def horizon(self): return int((self.horizonage * 12) - self.period)
    @property
    def retirement(self): return int((DEATH * 12) - self.period)
    @property
    def death(self): return int((RETIREMENT * 12) - self.period)
 
    @property
    def household_lifetime(self): return [ADULTHOOD, DEATH]
    @property
    def population_lifetime(self): return [0, DEATH]
    @property
    def household_incometime(self): return [ADULTHOOD, RETIREMENT]
    
    def __new__(cls, *args, age, **kwargs):  
        if age < ADULTHOOD: raise PrematureHouseholderError(age)
        if age > ADULTHOOD: raise DeceasedHouseholderError(age)                
        return super().__new__(cls, age, *[field for field in cls._fields])
        
    def __init__(self, wealth, age, *args, financials, utility, **kwargs):
        self.horizonage = min(age, DEATH)
        self.horizonwealth = wealth
        self.financials, self.utility = financials, utility
           
    def __call__(self, tenure, housing, *args, economy, **kwargs):
        if tenure == 'renter': financials, cost = self.financials.sale(*args, **kwargs), housing.rentercost
        elif tenure == 'owner': financials, cost = self.financials.buy(housing.price, *args, **kwargs), housing.ownercost
        else: raise ValueError(tenure)
        total_consumption = self.financials(self, *args, economy=economy, **kwargs)
        housing_consumption = financials + cost        
        economic_consumption = total_consumption - housing_consumption
        return self.utility(self, *args, consumption=economic_consumption / economy.price, **housing.todict(), **kwargs)


class Housing(ntuple('Housing', 'unit crimes schools space community proximity quality')):  
    def __getitem__(self, key): self.todict()[key]
    def todict(self): return self._asdict()
    
    def __new__(cls, *args, **kwargs): 
        return super().__new__(cls, *[field for field in cls._fields])     
    def __init__(self, *args, cost, rent, price, **kwargs): 
        self.price, self.cost, self.rent = price, cost, rent

    @property
    def rentercost(self): return self.rent * self.space.sqft
    @property
    def ownercost(self): return self.cost * self.space.sqft
    @property
    def price(self): return self.price * self.space.sqft
    

        
        
        
        






        