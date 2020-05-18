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


def createHousehold(geography, date, *args, **kwargs):
    financials = createFinancials(geography, date, *args, **kwargs)
    utility = createUtility(geography, date, *args, **kwargs)
    return Household(*args, geography=geography, date=date, financials=financials, utility=utility, **kwargs)    

    
class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


class Household(ntuple('Household', 'date geography age race language education children size')):
    ages = {'adulthood':15, 'retirement':65, 'dealth':95} 

    stringformat = 'Household|{age}YRS {education} {race} w/{size}PPL speaking {lanuguage} {children}'      
    def __str__(self): 
        householdstring = self.stringformat.format(age=self.age, race=self.race, language=self.language, education=self.education, children=self.children, size=self.size)
        financialstring = str(self.__financials)
        return '\n'.join([householdstring, financialstring])        
    
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography), 'utility':repr(self.__utility), 'financials':repr(self.__financials)}
        content.update({field:getattr(self, field) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))
    
    def __hash__(self):
        basis = (hash(self.date), hash(self.geography),)
        identity = (self.age, self.race, self.language, self.education, self.children, self.size,)
        content = (hash(self.__utility), hash(self.__financials),)
        return hash((self.__class__.__name__, *basis, *identity, *content))   
    
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
    def __getitem__(self, key): return self.__getattr__(key)
    def todict(self): return self._asdict()


    
    
    
    
    
    