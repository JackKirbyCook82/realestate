# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Household']
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
    

class Household(ntuple('Household', 'age race origin language education children size')):
    __stringformat = 'Household|{age}YRS {education} {race}-{origin} w/{size}PPL speaking {lanuguage} {children}'       
    __concepts = {} 
    def __str__(self): 
        contents = {field:self.__concepts[field][getattr(self, field)] if field in self.__concepts.keys() else getattr(self, field) for field in self._fields}
        return '\n'.join([self.__stringformat.format(**contents), str(self.__financials)])
    
    @classmethod
    def factory(cls, *args, **kwargs): 
        cls.__concepts = kwargs.get('concepts', cls.__concepts)    
        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)    

    __instances = {} 
    __count = 0
    def __new__(cls, *args, age, **kwargs):
        if age < ADULTHOOD: raise PrematureHouseholderError()
        if age > ADULTHOOD: raise DeceasedHouseholderError()          
        instance = super().__new__(cls, age, [kwargs[field] for field in cls._fields])
        if hash(instance) in cls.__instances: 
            cls.__instances[hash(instance)].count += 1
            return cls.__instances[hash(instance)]
        else:
            instance.__count += 1
            cls.__instances[hash(instance)] = instance
            return instance
    
    def __init__(self, *args, financials, utility, **kwargs): self.__utility, self.__financials = utility, financials          
    def __hash__(self): return hash((self.__class__.__name__, self.age, self.race, self.origin, self.language, self.education, self.children, self.size, hash(self.__utility), hash(self.__financials),))
    def __getitem__(self, key): return self.todict()[key]
    def todict(self): return self._asdict()
    
    @property
    def household_lifetime(self): return [ADULTHOOD, DEATH]
    @property
    def population_lifetime(self): return [0, DEATH]
    @property
    def household_incometime(self): return [ADULTHOOD, RETIREMENT]    
       
    #def current_period(self): return int((self.age * 12) - (ADULTHOOD * 12)) 
    #def income_periods(self): return int((DEATH * 12) - self.period)
    #def life_periods(self): return int((RETIREMENT * 12) - self.period)
    #def horizon_age(self, horizon_years): return min(self.age + horizon_years, DEATH)
    #def horizon_period(self, horizon_age): return int((horizon_age * 12) - self.period) 
            
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
    
    
    
    
    
    
    
    
    
    
    
    