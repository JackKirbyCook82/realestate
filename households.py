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
__all__ = ['createHousehold', 'Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


def createHousehold(geography, date, *args, **kwargs):  
    financials = createFinancials(geography, date, *args, **kwargs)
    utility = createUtility(geography, date, *args, **kwargs)      
    return Household(*args, geography=geography, date=date, financials=financials, utility=utility, **kwargs)    

def createHouseholdKey(*args, date, age, race, language, education, children, size, financials, utility, variables, **kwargs):
    age_index = variables['age'](age).index
    race_index =variables['race'](race).index
    language_index = variables['language'](language).index
    education_index = variables['education'](education).index
    children_index = variables['children'](children).index
    size_index = variables['size'](size).index
    return (date.index, age_index, race_index, language_index, education_index, children_index, size_index, hash(financials.key), hash(utility.key),)


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


class Household(ntuple('Household', 'date age race language education children size financials utility')):
    __instances = {}     
    __stringformat = 'Household[{count}]|{race} HH speaking {language} {children}, {age}, {size}, {education} Education'          
    def __str__(self):  
        values = {field:getattr(self, field) for field in ('age', 'race', 'language', 'education', 'children', 'size',)}
        content = {field:self.__variables[field](value) for field, value in values.items()}
        householdstring = self.__stringformat.format(count=self.count, **content)
        financialstring = str(self.financials)
        return '\n'.join([householdstring, financialstring])        
    
    def __repr__(self): 
        content = {'utility':repr(self.__utility), 'financials':repr(self.__financials)}
        content.update({field:repr(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    @property
    def key(self): return hash(createHouseholdKey(**self.todict(), variables=self.__variables))   
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return all([self.key == other.key, self.risktolerance == other.risktolerance, self.rates == other.rates])
    
    @property
    def risktolerance(self): return self.__risktolerance
    @property
    def rates(self): return dict(discountrate=self.__discountrate, wealthrate=self.__wealthrate, valuerate=self.__valuerate, incomerate=self.__incomerate)
    
    @property
    def count(self): return self.__count    
    def __new__(cls, *args, lifetimes, **kwargs):
        if kwargs['age'] < lifetimes['adulthood']: raise PrematureHouseholderError()
        if kwargs['age'] > lifetimes['death']: raise DeceasedHouseholderError()              
        key = hash(createHouseholdKey(*args, **kwargs))
        try: return cls.__instances[key]
        except KeyError: 
            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
            cls.__instances[key] = newinstance
            return newinstance
    
    def __init__(self, *args, risktolerance, discountrate, wealthrate, valuerate, incomerate, variables, **kwargs):                
        self.__discountrate, self.__wealthrate, self.__valuerate, self.__incomerate = discountrate, wealthrate, valuerate, incomerate
        self.__risktolerance = risktolerance       
        self.__variables = variables
        try: self.__count = self.__count + 1
        except AttributeError: self.__count = 1
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    


    
    
    
    
    
    