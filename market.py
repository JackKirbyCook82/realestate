# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.strings import uppercase
from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Rates', 'Durations', 'Economy', 'Loan', 'Financials', 'Housing', 'Household', 'InsufficientFundsError', 'InsufficientCoverageError', 'UnstableLifeStyleError']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


class Rates(ntuple('Rates', 'discount wealth value income mortgage studentloan debt')): 
    @keydispatcher
    @classmethod
    def convertfrom(cls, basis, rate): raise KeyError(basis)
    @convertfrom('monthly')
    @classmethod
    def convertfrom_monthly(cls, rate): return rate
    @convertfrom('yearly')
    @classmethod
    def convertfrom_yearly(cls, rate): return pow(rate + 1, 1/12) - 1
    
    def __new__(cls, basis, *args, **kwargs): return super().__new__(cls, *[float(cls.convertfrom(basis, kwargs[rate])) for rate in cls._fields])
    def __repr__(self): return '{}(discount={}, wealth={}, value={}, income={}, mortgage={}, studentloan={}, debt={})'.format(self.__class__.__name__, *self._fields)
    
    def theta(self, risk): return (self.wealth - self.discount) / risk    
    def income_integral(self, horizon): return (1 - pow(1 + self.income - self.wealth, horizon)) / (self.income - self.wealth)
    def consumption_integal(self, horizon, *args, economy, **kwargs): return (1 - pow(1 + self.theta(economy.risk) - self.wealth, horizon)) / (self.theta(economy.risk) - self.wealth)
    
    def mortgage_integral(self, horizon): return self.loan_integral(self, 'mortgage', horizon) 
    def studentloan_integral(self, horizon): return self.loan_integral(self, 'studentloan', horizon) 
    def debt_integal(self, horizon): return self.loan_integral(self, 'debt', horizon) 
    
    def loan_integral(self, loan, horizon): return self.__loanfactor(loan) * (pow(1 - self.wealth, horizon) - 1) / self.wealth
    def __loanfactor(self, loan, horizon): return (getattr(self, loan) * pow(1 + getattr(self, loan), horizon)) / (pow(1 + getattr(self, loan), horizon) - 1)


class Durations(ntuple('Duration', 'life income mortgage studentloan debt')):
    @keydispatcher
    @classmethod
    def convertfrom(cls, basis, rate): raise KeyError(basis)
    @convertfrom('monthly')
    @classmethod
    def convertfrom_monthly(cls, duration): return duration
    @convertfrom('yearly')
    @classmethod
    def convertfrom_yearly(cls, duration): return duration * 12
    
    def __new__(cls, basis, *args, **kwargs): return super().__new__(cls, *[int(cls.convertfrom(basis, kwargs[rate])) for rate in cls._fields])
    def __repr__(self): return '{}(life={}, income={}, mortgage={}, studentloan={}, debt={})'.format(self.__class__.__name__, *self._fields)
    def __call__(self, key, *args, **kwargs): return self.execute(key, *args, **kwargs)

    @keydispatcher
    def execute(self, key, *args, **kwargs): raise KeyError(key)
    @execute('life')
    def __life(self, period, horizon, *args, **kwargs): return min(period + horizon, self.life)
    @execute('income')
    def __income(self, period, horizon, *args, **kwargs): return min(period + horizon, self.income)
    @execute('mortgage')
    def __mortgage(self, period, horizon, duration, *args, **kwargs): return min(self.__life(period, horizon), duration)
    @execute('studentloan')
    def __studentloan(self, period, horizon, duration, *args, **kwargs): return min(self.__life(period, horizon), duration)
    @execute('debt')
    def __debt(self, period, horizon, duration, *args, **kwargs): return min(self.__life(period, horizon), duration)
    

class Economy(ntuple('Economy', 'rates risk price commisions financing coverage loantovalue')):
    def __repr__(self): return '{}(rates={}, commisions={}, financing={}, coverage={}, loantovalue={})'.format(self.__class__.__name__, repr(self.rates), *self._fields[1:])
    def __new__(cls, rates, commisions, financing, coverage, loantovalue):
        assert isinstance(rates, Rates)
        return super().__new__(cls, rates, commisions, financing, coverage, loantovalue)


class Loan(ntuple('Loan', 'name balance rate duration')):
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
    @property
    def coverage(self): return self.income / (self.mortgage.payment + self.studentloan.payment + self.debt.payment)
    @property
    def loantovalue(self): return self.mortgage / self.value

    def __new__(cls, wealth, income, value, mortgage, studentloan, debt):        
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
    def buy(self, value, *args, economy, durations, **kwargs): 
        closingcost = self.__commisions(value, economy.commisions, economy.financing)
        downpayment = self.__downpayment(value, economy.loantovalue)
        mortgage = Loan('mortgage', value - downpayment, economy.rates.mortgage, durations.mortgage)
        newfinancials = self.__class__(self.wealth - downpayment - closingcost, self.income, value, mortgage, self.studentloan, self.debt)
        if newfinancials.wealth < 0: raise InsufficientFundsError(newfinancials)  
        if newfinancials.coverage < economy.coverage: raise InsufficientCoverageError(newfinancials, economy.coverage)
        return newfinancials
          
    def __call__(self, wealth, period, horizon, *args, economy, durations, **kwargs): 
        w = self.wealth - (wealth / pow(1 + economy.rates.wealth, durations.life(period, horizon))) 
        i = economy.rates.income_integral(durations('income', period, horizon))
        c = economy.rates.consumption_integal(durations('life', period, horizon), economy=economy)
        m = economy.rates.mortgage_integral(durations('mortgage', period, horizon, self.mortgage.duration))
        s = economy.rates.studentloan_integral(durations('studentloan', period, horizon, self.studentloan.duration))
        d = economy.rates.debt_integal(durations('debt', period, horizon, self.debt.duration))        
        consumption = (w + (i * self.income) - (m * self.mortgage) - (s * self.studentloan) - (d * self.debt)) / c
        if consumption < 0: raise UnstableLifeStyleError(consumption)
        return consumption
        

class Household(ntuple('Household', 'period race education children size')):
    def __new__(cls, *args, age, race, education, children, size, **kwargs):
        return super().__new__(cls, age, race, education, children, size)
        
    def __init__(self, wealth, horizon, *args, financials, utility, **kwargs):
        self.wealth, self.horizon = wealth, horizon
        self.financials, self.utility = financials, utility
           
    def __call__(self, tenure, housing, *args, economy, durations, **kwargs):
        if tenure == 'renter': 
            financials = self.financials.sale(*args, **kwargs)
            cost = housing.rentercost
        elif tenure == 'owner': 
            financials = self.financials.buy(housing.price, *args, **kwargs)
            cost = housing.ownercost
        else: raise ValueError(tenure)
        total_consumption = self.financials(self.wealth, self.period, self.horizon, *args, econcomy=economy, durations=durations, **kwargs)
        housing_consumption = financials + cost        
        economic_consumption = total_consumption - housing_consumption
        return self.utility(consumption=economic_consumption / economy.price, **housing.todict())


class Housing(ntuple('Housing', 'unit crime school space community proximity quality')):  
    def todict(self): return self._asdict()
    
    def __new__(cls, *args, unit, crime, school, space, community, proximity, quality, **kwargs): 
        return super().__new__(cls, unit, crime, school, space, community, proximity, quality)   
    
    def __init__(self, *args, cost, rent, price, **kwargs): 
        self.price, self.cost, self.rent = price, cost, rent

    @property
    def rentercost(self): return self.rent * self.space.sqft
    @property
    def ownercost(self): return self.cost * self.space.sqft
    @property
    def price(self): return self.price * self.space.sqft
    

        
        
        
        






        