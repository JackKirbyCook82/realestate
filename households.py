# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from realestate.finance import Financials
from realestate.finance import Utility

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_monthrate= {'year': lambda rate: float(pow(rate + 1, 1/12) - 1), 'month': lambda rate: float(rate)} 
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass
 

class Household(ntuple('Household', 'age race origin language education children size')):
    ages = {'adulthood':15, 'retirement':65, 'dealth':95}
    stringformat = 'Household|{age}YRS {education} {race}-{origin} w/{size}PPL speaking {lanuguage} {children}'       
    concepts = {} 
    
    @classmethod
    def setup(cls, *args, **kwargs): 
        attrs = {'concepts':kwargs.get('concepts', cls.concepts), 
                 'stringformat':kwargs.get('stringformat', cls.stringformat), 
                 'ages':{key:kwargs.get(key, value) for key, value in cls.ages.items()}}
        return type(cls.__name__, (cls,), attrs)    
    
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
    
    def __str__(self): 
        contents = {field:self.concepts[field][getattr(self, field)] if field in self.concepts.keys() else getattr(self, field) for field in self._fields}
        return '\n'.join([self.stringformat.format(**contents), str(self.__financials)])    
    
    def __init__(self, *args, financials, utility, **kwargs): self.__utility, self.__financials = utility, financials          
    def __hash__(self): return hash((self.__class__.__name__, self.age, self.race, self.origin, self.language, self.education, self.children, self.size, hash(self.__utility), hash(self.__financials),))
    def __getitem__(self, key): return self.todict()[key]
    def todict(self): return self._asdict()

    @classmethod
    def create(cls, *args, age, education, race, origin, language, children, size, **kwargs):
        financials = Financials.create(*args, age=age, education=education, ages=cls.ages, **kwargs)
        utility = Utility.create(*args, **kwargs)
        return cls(age=age, race=race, origin=origin, language=language, education=education, children=children, size=size, financials=financials, utility=utility)

        
    
    
    
    
    
    
    
    
    
    
    
    
    