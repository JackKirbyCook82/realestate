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

def createHouseholdKey(*args, date, geography, age, race, language, education, children, size, utility, financials, **kwargs):
    basis = (hash(date), hash(geography),)
    identity = (age, race, language, education, children, size,)
    content = (hash(utility), hash(financials),)
    return ('Household', *basis, *identity, *content,) 

    
class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


class Household(ntuple('Household', 'date geography age race language education children size')):
    __instances = {}     
    __ages = {'adulthood':15, 'retirement':65, 'dealth':95} 

    stringformat = 'Household|{age} {education} {race} w/{size} speaking {lanuguage} {children}, [{count}]'      
    def __str__(self): 
        householdstring = self.stringformat.format(count=self.count, age=self.age, race=self.race, language=self.language, education=self.education, children=self.children, size=self.size)
        financialstring = str(self.__financials)
        return '\n'.join([householdstring, financialstring])        
    
    def __hash__(self): return hash(createHouseholdKey(**self.todict()))    
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography), 'utility':repr(self.__utility), 'financials':repr(self.__financials)}
        content.update({field:str(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    @property
    def count(self): return self.__count
    def addcount(self): self.__count += 1
    
    def __new__(cls, *args, age, **kwargs):
        if age < cls.__ages['adulthood']: raise PrematureHouseholderError()
        if age > cls.__ages['death']: raise DeceasedHouseholderError()              
        key = createHouseholdKey(*args, **kwargs)
        if hash(key) in cls.__instances: 
            cls.__instances[key].addcount()
            return cls.__instances[key]
        else:
            newinstance = super().__new__(cls, age=age, **{field:kwargs[field] for field in cls._fields})
            cls.__instances[key] = newinstance
            return newinstance
    
    def __init__(self, *args, financials, utility, **kwargs): 
        self.__utility, self.__financials = utility, financials                 
        self.__count = 1
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    


    
    
    
    
    
    