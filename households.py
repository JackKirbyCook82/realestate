# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from realestate.finance import createFinancials
from realestate.utility import createUtility

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['createHousehold']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_monthrate= {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}


# geography, date 
# horizon 
# broker, schools, banks
# age, education, income, equity, value, yearoccupied, race, language, children, size
# incomerate, valuerate, wealthrate, discountrate, riskrate
    
def createHousehold(geography, date, *args, **kwargs):
    pass
    
    
class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


class Household(ntuple('Household', 'age race language education children size')):
    ages = {'adulthood':15, 'retirement':65, 'dealth':95}
    stringformat = 'Household|{age}YRS {education} {race} w/{size}PPL speaking {lanuguage} {children}'      
    def __str__(self): return '\n'.join([self.stringformat.format(**{field:getattr(self, field) for field in self._fields}), str(self.__financials)])        
    
    __instances = {} 
    __count = 0
    @property
    def count(self): return self.__count 
    
    def __new__(cls, *args, age, **kwargs):
        if age < cls.ages['adulthood']: raise PrematureHouseholderError()
        if age > cls.ages['death']: raise DeceasedHouseholderError()          
        instance = super().__new__(cls, age=age, **{field:kwargs[field] for field in cls._fields})
        if hash(instance) in cls.__instances: 
            cls.__instances[hash(instance)].count += 1
            return cls.__instances[hash(instance)]
        else:
            instance.__count += 1
            cls.__instances[hash(instance)] = instance
            return instance
    
    def __init__(self, *args, financials, utility, **kwargs): self.__utility, self.__financials = utility, financials          
    def __hash__(self): return hash((self.__class__.__name__, self.age, self.race, self.language, self.education, self.children, self.size, hash(self.__utility), hash(self.__financials),))
    def __getitem__(self, key): return self.__getattr__(key)
    def todict(self): return self._asdict()

#    @classmethod
#    def create(cls, *args, age, education, race, language, children, size, **kwargs):
#        financials = Financials.create(*args, age=age, education=education, ages=cls.ages, **kwargs)
#        utility = Utility.create(*args, **kwargs)
#        return cls(age=age, race=race, language=language, education=education, children=children, size=size, financials=financials, utility=utility)


    
    
    
    
    
    
    