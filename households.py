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
    rates = {ratekey:kwargs.pop(ratekey)(date.index, units='month') for ratekey in ('discountrate', 'wealthrate', 'valuerate', 'incomerate',)}
    financials = createFinancials(geography, date, *args, **rates, **kwargs)
    utility = createUtility(geography, date, *args, **kwargs)
    return Household(*args, geography=geography, date=date, financials=financials, utility=utility, **rates, **kwargs)    

def createHouseholdKey(*args, age, race, language, education, children, size, **kwargs):
    return (age.index, race.index, language.index, education.index, children.index, size.index,)


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


class Household(ntuple('Household', 'date geography age race language education children size')):
    __instances = {}     
    __stringformat = 'Household[{count}]|{race} HH speaking {language} {children}, {age}, {size}, {education} Education'          
    def __str__(self): 
        householdstring = self.__stringformat.format(count=self.count, age=self.age, race=self.race, language=self.language, education=self.education, children=self.children, size=self.size)
        financialstring = str(self.__financials)
        return '\n'.join([householdstring, financialstring])        
    
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography), 'utility':repr(self.__utility), 'financials':repr(self.__financials)}
        content.update({field:repr(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    @property
    def count(self): return self.__count

    def __hash__(self): return hash(createHouseholdKey(**self.todict()))
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other):
        if not isinstance(other, type(self)): raise TypeError(type(other))
        return hash(self) == hash(other)  
    
    def __new__(cls, *args, ages, **kwargs):
        if kwargs['age'].value < ages['adulthood']: raise PrematureHouseholderError()
        if kwargs['age'].value > ages['death']: raise DeceasedHouseholderError()              
        key = hash(createHouseholdKey(*args, **kwargs))
        try: return cls.__instances[key]
        except KeyError: 
            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
            cls.__instances[key] = newinstance
            return newinstance
    
    def __init__(self, *args, financials, utility, risktolerance, discountrate, wealthrate, valuerate, incomerate, **kwargs): 
        self.__utility, self.__financials = utility, financials                 
        self.__discountrate, self.__risktolerance = discountrate, risktolerance
        self.__wealthrate, self.__valuerate, self.__incomerate = wealthrate, valuerate, incomerate
        try: self.__count = self.__count + 1
        except AttributeError: self.__count = 1
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    


    
    
    
    
    
    