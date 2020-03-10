# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Participants
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.strings import uppercase

from realestate.finance import InsufficientFundsError, InsufficientCoverageError, UnstableLifeStyleError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Market', 'Housing', 'Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


ADULTHOOD = 15
RETIREMENT = 65
DEATH = 95

_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


class PrematureHouseholderError(Exception):
    def __init__(self, age): super().__init__('{} < {}'.format(age, ADULTHOOD))
class DeceasedHouseholderError(Exception):
    def __init__(self, age): super().__init__('{} > {}'.format(age, DEATH))
    

class Household(ntuple('Household', 'age race origin language english education children size')):
    stringformat = 'Household|{age}YRS {education} {race}-{origin} w/{size}PPL speaking {lanuguage} {children}'
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self.todict().items()})
    def __init__(self, *args, financials, utility, **kwargs): self.utility, self.financials = utility, financials    
    def __new__(cls, *args, age, **kwargs):
        if age < ADULTHOOD: raise PrematureHouseholderError(age)
        if age > ADULTHOOD: raise DeceasedHouseholderError(age)                   
        return super().__new__(cls, age, [kwargs[field] for field in cls._fields])
     
    def todict(self): return self._asdict()
    def __getitem__(self, key): return self.todict()[key]
        
    def current_period(self): return int((self.age * 12) - (ADULTHOOD * 12)) 
    def income_periods(self): return int((DEATH * 12) - self.period)
    def life_periods(self): return int((RETIREMENT * 12) - self.period)
    def horizon_age(self, horizon_years): return min(self.age + horizon_years, DEATH)
    def horizon_period(self, horizon_age): return int((horizon_age * 12) - self.period) 
    
    @property
    def household_lifetime(self): return [ADULTHOOD, DEATH]
    @property
    def population_lifetime(self): return [0, DEATH]
    @property
    def household_incometime(self): return [ADULTHOOD, RETIREMENT]
         
    def __call__(self, housing, horizon_wealth, horizon_years, *args, economy, **kwargs):
        horizon_periods, income_periods = self.horizon_period(self.horizon_age(horizon_years)), self.income_periods()
        if housing.tenure == 'renter': 
            financials, cost = self.financials.sale(*args, **kwargs), housing.rentercost
        elif housing.tenure == 'owner': 
            try: financials, cost = self.financials.buy(housing.price, *args, **kwargs), housing.ownercost
            except InsufficientFundsError: return 0
            except InsufficientCoverageError: return 0
        else: raise ValueError(housing.tenure)
        try: total_consumption = self.financials(horizon_periods, income_periods, horizon_wealth, *args, economy=economy, **kwargs)
        except UnstableLifeStyleError: return 0
        housing_consumption = financials + cost        
        economic_consumption = total_consumption - housing_consumption
        return self.utility(self, *args, consumption=economic_consumption/economy.price, **housing.todict(), **kwargs)


class Housing(ntuple('Housing', 'unit cost geography crimes schools space community proximity quality')):  
    stringformat = 'Housing|{tenure}{unit} ${cost} with {sqft}SQFT in {geography} builtin {year}'
    def __str__(self): 
        if self.tenure == 'renter': cost = self.rentercost()
        elif self.tenure == 'owner': cost = self.price()
        else: raise ValueError(self.tenure)
        content = dict(tenure=uppercase(self.tenure), unit=uppercase(self.unit), sqft=self.sqft, year=self.year, geography=str(self.geography), cost=cost)
        return self.stringformat.format(**content)

    __instances, __count = {}, 0
    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls, [kwargs[field] for field in cls._fields])
        if hash(instance) in cls.__instances: 
            cls.__instances[hash(instance)].count += 1
            return cls.__instances[hash(instance)]
        else:
            instance.__count += 1
            cls.__instances[hash(instance)] = instance
            return instance
        
    def __init__(self, tenure, sqftrent, sqftprice, *args, **kwargs):
        self.__tenure = tenure
        self.__sqftrent = sqftrent
        self.__sqftprice = sqftprice
        
    def todict(self): return self._asdict()
    def __getitem__(self, key): return self.todict()[key]    
    def __hash__(self): 
        items = [hash(getattr(self, item)) for item in ('crimes', 'schools', 'space', 'comunity', 'proximity', 'quality')]
        return hash((self.__class__.__name__, self.unit, self.cost, *items,))

    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other):
        assert isinstance(other, type(self))
        return all([getattr(other, field) == getattr(self, field) for field in self._fields])

    def set_sqftrent(self, sqftrent): self.__sqftrent = sqftrent
    def set_sqftprice(self, sqftprice): self.__sqftprice = sqftprice
    def set_tenure(self, tenure): self.__tenure = tenure
    
    @property
    def tenure(self): return self.__tenure
    @property
    def count(self): return self.__count       
    @property
    def year(self): return self.quality.yearbuilt
    @property
    def sqft(self): return self.space.sqft
    @property
    def ownercost(self): return self.costsqft * self.sqft    
    @property
    def rentercost(self): return self.__sqftrent * self.sqft
    @property
    def price(self): return self.__sqftprice * self.sqft  
    @property
    def geoID(self): return self.geography.geoID


class Market(object):
    def __init__(self, households=[], housings=[]):
        assert all([isinstance(household, Household) for household in _aslist(households)])
        assert all([isinstance(housing, Housing) for housing in _aslist(housings)])
        self.__housing = _aslist(housings)
        self.__households = _aslist(households)
        
    def __call__(self, *args, **kwargs):
        pass





        



















