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
    
#def createHouseholdKey(*args, date, geography, age, race, language, education, children, size, **kwargs):
#    return ('Household', hash(geography), hash(date), age.index, race.index, education.index, children.index, size.index,) 

    
class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


class Household(ntuple('Household', 'date geography age race language education children size')):
#    __instances = {}     
    __stringformat = 'Household[count]|{language} speaking {race}, {age}, {children} {size}, {education} education'          
    def __str__(self): 
        householdstring = self.__stringformat.format(count=self.count, age=self.age, race=self.race, language=self.language, education=self.education, children=self.children, size=self.size)
        financialstring = str(self.__financials)
        return '\n'.join([householdstring, financialstring])        
    
#    def __hash__(self): raise Exception('HASH TABLE REQUIRED')
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography), 'utility':repr(self.__utility), 'financials':repr(self.__financials)}
        content.update({field:repr(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

#    @classmethod
#    def counts(cls): return [instance.count for instance in cls.__instances.values()]

#    @property
#    def count(self): return self.__count
#    def addcount(self): self.__count += 1
    
#    def __new__(cls, *args, economy, **kwargs):
#        if kwargs['age'].value < economy.ages['adulthood']: raise PrematureHouseholderError()
#        if kwargs['age'].value > economy.ages['death']: raise DeceasedHouseholderError()              
#        key = createHouseholdKey(*args, **kwargs)
#        if hash(key) in cls.__instances.keys(): 
#            cls.__instances[key].addcount()
#            return cls.__instances[key]
#        else:
#            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
#            cls.__instances[key] = newinstance
#            return newinstance
    
    def __init__(self, *args, financials, utility, **kwargs): 
        self.__utility, self.__financials = utility, financials                 
        self.__count = 1
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    


    
    
    
    
    
    