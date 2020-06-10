# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from realestate.finance import Financials
from realestate.utility import Housing_UtilityIndex, Consumption_UtilityIndex
from realestate.utility import Crime_UtilityIndex, School_UtilityIndex, Quality_UtilityIndex, Space_UtilityIndex, Proximity_UtilityIndex, Community_UtilityIndex
from realestate.utility import CobbDouglas_UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


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

#    @property
#    def netconsumption(self): return self.financials.netconsumption

    @classmethod
    def create(cls, geography, date, *args, household={}, financials={}, rates, lifetimes, **kwargs):  
        assert isinstance(household, dict) and isinstance(financials, dict)
        income_horizon = max((lifetimes['retirement'] - household['age']) * 12, 0)
        consumption_horizon = max((lifetimes['death'] - household['age']) * 12, 0)    
        financials = Financials(income_horizon, consumption_horizon, *args, **financials, **kwargs)
        consumption = Consumption_UtilityIndex(amplitude=1, tolerances={})
        housing = Housing_UtilityIndex(amplitude=1, tolerance={})        
        indexes = dict(consumption=consumption, housing=housing)
        utility = CobbDouglas_UtilityFunction(amplitude=1, subsistences={}, weights={}, diminishrate=1, indexes=indexes)   
        return cls(*args, geography=geography, date=date, **household, financials=financials, utility=utility, **rates, lifetimes=lifetimes, **kwargs)            
#        space = Space_UtilityIndex(amplitude=1, tolerances={})
#        quality = Quality_UtilityIndex(amplitude=1, tolerances={})
#        crime = Crime_UtilityIndex(amplitude=1, tolerances={})
#        school = School_UtilityIndex(amplitude=1, tolerances={})      
#        proximity = Proximity_UtilityIndex(amplitude=1, tolerances={})
#        community = Community_UtilityIndex(amplitude=1, tolerances={})        
    

    
    
    
    
    
    