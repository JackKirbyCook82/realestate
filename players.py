# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Player Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple
import math

from utilities.strings import uppercase
from realestate.finance import Loan

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['MortgageBank', 'CreditBank', 'StudentLoanBank', 'Broker', 'Housing', 'Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


ADULTHOOD = 15
RETIREMENT = 65
DEATH = 95

_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_monthrate= {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass
    

class Bank(ntuple('bank', 'type name rate duration')):
    stringformat = '{name}|{type}bank providing {rate}%/MO for {duration}-MOS' 
    def __str__(self): return self.stringformat.format(**{'type':uppercase(self.type)}, name=self.name, rate=self.rate, duration=self.duration)        
    def __repr__(self): return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value] for key, value in self._asdict().items())]))      
    def __new__(cls, *args, basis='month', rate, duration, **kwargs): 
        kwargs.update({'rates':_monthrate[basis](kwargs['rates']), 'duration':_monthduration[basis](kwargs['duration'])})
        return super().__new__(cls, **kwargs)                   
    
    def loan(self, amount): return Loan(self.type, amount, self.rate, self.duration)

    
class CreditBank(Bank): 
    def __new__(cls, *args, **kwargs): return super().__new__(cls, *args, **{'type':'credit'}, **kwargs)
   
    
class StudentLoanBank(Bank): 
    def __new__(cls, *args, **kwargs): return super().__new__(cls, *args, **{'type':'studentloan'}, **kwargs)
    
    
class MortgageBank(Bank): 
    def __new__(cls, *args, **kwargs): return super().__new__(cls, *args, **{'type':'mortgage'}, **kwargs)
    def __init__(self, *args, financing, coverage, loantovalue, **kwargs): 
        self.financing, self.coverage, self.loantovalue = financing, coverage, loantovalue

    def qualify(self, coverage): return coverage >= self.coverage
    def downpayment(self, value): return value * (1 - self.loantovalue)
    def cost(self, amount): return amount * (1 + self.financing)


class Broker(ntuple('Broker', 'commisions')): 
    def cost(self, amount): return amount * (1 + self.commisions)


class Household(ntuple('Household', 'age race origin language education children size')):
    __stringformat = 'Household|{age}YRS {education} {race}-{origin} w/{size}PPL speaking {lanuguage} {children}'       
    __concepts = {} 
    def __str__(self): 
        contents = {field:self.__concepts[field][getattr(self, field)] if field in self.__concepts.keys() else getattr(self, field) for field in self._fields}
        householdstr = self.__stringformat.format(**contents)
        financialstr = str(self.__financials)
        return '\n'.join([householdstr, financialstr])
    
    @classmethod
    def factory(cls, *args, **kwargs): 
        cls.__concepts = kwargs.get('concepts', cls.__concepts)    
        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)    
             
    def __new__(cls, *args, age, **kwargs):
        if age < ADULTHOOD: raise PrematureHouseholderError()
        if age > ADULTHOOD: raise DeceasedHouseholderError()                   
        return super().__new__(cls, age, [kwargs[field] for field in cls._fields])    
    
    def __init__(self, *args, financials, utility, date, **kwargs): 
        self.__utility, self.__financials, self.__date = utility, financials, date            
    
    def todict(self): return self._asdict()
    def __getitem__(self, key): return self.todict()[key]
        
    #def current_period(self): return int((self.age * 12) - (ADULTHOOD * 12)) 
    #def income_periods(self): return int((DEATH * 12) - self.period)
    #def life_periods(self): return int((RETIREMENT * 12) - self.period)
    #def horizon_age(self, horizon_years): return min(self.age + horizon_years, DEATH)
    #def horizon_period(self, horizon_age): return int((horizon_age * 12) - self.period) 
    
    @property
    def household_lifetime(self): return [ADULTHOOD, DEATH]
    @property
    def population_lifetime(self): return [0, DEATH]
    @property
    def household_incometime(self): return [ADULTHOOD, RETIREMENT]
         
    #def utility(self, housing, tenure, horizon, wealth_multiple, *args, economy, **kwargs):
    #    horizon_periods, income_periods = self.horizon_period(self.horizon_age(horizon)), self.income_periods()
    #    if tenure == 'renter': financials, cost = self.__financials.sale(*args, **kwargs), housing.rentercost
    #    elif tenure == 'owner': financials, cost = self.__financials.buy(housing.price, *args, **kwargs), housing.ownercost
    #    total_consumption = self.__financials.consumption(horizon_periods, income_periods, wealth_multiple, *args, economy=economy, **kwargs)
    #    housing_consumption = financials + cost        
    #    economic_consumption = total_consumption - housing_consumption
    #    return self.__utility(self, *args, consumption=economic_consumption/economy.price, **housing.todict(), date=self.__date, **kwargs)
    
    #def __call__(self, duration_months, *args, **kwargs): 
    #    self.__date = self.__date.add(months=duration_months)
    #    self.__financials = self.__financials(duration_months, *args, **kwargs)
    #    return self
    

class Housing(ntuple('Housing', 'unit sqftcost geography crimes schools space community proximity quality')):     
    __stringformat = 'Housing|{unit} with {sqft}SQFT in {geography} builtin {year}|${rent:.0f}/MO Rent|${price:.0f} Purchase' 
    __concepts = {}    
    def __str__(self): 
        unit = self.__concepts['unit'][self.unit] if 'unit' in self.__concepts.keys() else self.unit
        content = dict(sqft=self.sqft, year=self.year, geography=str(self.geography), rent=self.rentercost, price=self.price)
        return self.__stringformat.format(unit=unit, **content)
    
    @classmethod
    def factory(cls, *args, **kwargs): 
        cls.__concepts = kwargs.get('concepts', cls.__concepts)    
        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)    

    __instances = {} 
    __count = 0
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, [kwargs[field] for field in cls._fields])
        if hash(instance) in cls.__instances: 
            cls.__instances[hash(instance)].count += 1
            return cls.__instances[hash(instance)]
        else:
            instance.__count += 1
            cls.__instances[hash(instance)] = instance
            return instance
        
    def __init__(self, sqftprice, sqftrent,  *args, rentalrate, **kwargs):
        assert 0 < rentalrate < 1
        self.__sqftrent, self.__sqftprice = sqftrent, sqftprice
        self.__rentalrate, self.__ownerrate = rentalrate, property(lambda: 1 - self.__rentalrate)
        
    def todict(self): return self._asdict()
    def __getitem__(self, key): return self.todict()[key]    
    def __hash__(self): 
        items = [hash(getattr(self, item)) for item in ('crimes', 'schools', 'space', 'comunity', 'proximity', 'quality')]
        return hash((self.__class__.__name__, self.unit, self.cost, *items,))

    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other):
        assert isinstance(other, type(self))
        return all([getattr(other, field) == getattr(self, field) for field in self._fields])
    
    @property
    def count(self): return self.__count     
    @property
    def rentercount(self): return math.floor(self.__count * self.__rentalrate)
    @property
    def ownercount(self): return math.ceil(self.__count * self.__ownerrate)
    
    @property
    def geoID(self): return self.geography.geoID    
    @property
    def year(self): return self.quality.yearbuilt
    @property
    def sqft(self): return self.space.sqft
    
    @property
    def price(self): return self.__sqftprice * self.sqft      
    @property
    def ownercost(self): return self.__sqftcost * self.sqft    
    @property
    def rentercost(self): return self.__sqftrent * self.sqft

    #def __call__(self, duration_months, *args, pricerate, rentrate, **kwargs): 
    #    self.__sqftrent = self.__sqftrent * pow(1 + pricerate, duration_months)
    #    self.__sqftprice = self.__sqftprice * pow(1 + rentrate, duration_months)
    #    return self









