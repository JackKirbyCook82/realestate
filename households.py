# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from realestate.finance import Financials
from realestate.utility import UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


def createHouseholdKey(*args, date, financials, utility, variables, **kwargs):
    indexes = []
    for key in ('age', 'race', 'language', 'education', 'children', 'size',):
        if key in variables.keys(): indexes.append(variables[key](kwargs[key]).index)
        else: indexes.append(kwargs[key])
    return (date.index, *indexes, financials.key, utility.key,)


class Household(ntuple('Household', 'date age race language education children size financials utility')):
    __lifetimes = {'adulthood':15, 'retirement':65, 'death':95}  
    __utility = 'cobbdouglas'
    __parameters = ('spending', 'crime', 'school', 'quality', 'space', 'proximity', 'community',)
    __variables = dict()
    
    @classmethod
    def customize(cls, *args, **kwargs):
        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)
        cls.__variables = kwargs.get('variables', cls.__variables)
        cls.__lifetimes = kwargs.get('lifetimes', cls.__lifetimes)   
        cls.__utility = kwargs.get('utility', cls.__utility)
        cls.__parameters = kwargs.get('parameters', cls.__parameters)
    
    __stringformat = 'Household[{count}]|{race} HH speaking {language} {children}, {age}, {size}, {education} Education'          
    def __str__(self):  
        content = {field:getattr(self, field) for field in ('age', 'race', 'language', 'education', 'children', 'size',)}
        content = {key:self.__variables[key](value) if key in self.__variables.keys() else value for key, value in content.items()}        
        householdstring = self.__stringformat.format(count=self.count, **content)
        financialstring = str(self.financials)
        return '\n'.join([householdstring, financialstring])        
    
    def __repr__(self): 
        content = {'utility':repr(self.utility), 'financials':repr(self.financials)}
        content.update({field:repr(getattr(self, field)) for field in self._fields if field not in content.keys()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    __instances = {}       
    @property
    def count(self): return self.__count    
    def __new__(cls, *args, **kwargs):
        if kwargs['age'] < cls.__lifetimes['adulthood']: raise PrematureHouseholderError()
        if kwargs['age'] > cls.__lifetimes['death']: raise DeceasedHouseholderError()              
        key = hash(createHouseholdKey(*args, **kwargs, variables=cls.__variables))
        try: return cls.__instances[key]
        except KeyError: 
            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
            cls.__instances[key] = newinstance
            return newinstance
    
    def __init__(self, *args, count=1, **kwargs):                    
        try: self.__count = self.__count + count
        except AttributeError: self.__count = count
    
    @property
    def key(self): return hash(createHouseholdKey(**self.todict(), variables=self.__variables))   
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return self.key == other.key    
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    @classmethod
    def create(cls, *args, date, household={}, financials={}, **kwargs):
        assert isinstance(household, dict) and isinstance(financials, dict)
        income_horizon = max((cls.__lifetimes['retirement'] - household['age']) * 12, 0)
        consumption_horizon = max((cls.__lifetimes['death'] - household['age']) * 12, 0)   
        financials = Financials.create(income_horizon, consumption_horizon, date=date, **financials)
        utility = UtilityFunction.getfunction(cls.__utility).create(cls.__parameters, **household)
        return cls(*args, date=date, **household, financials=financials, utility=utility, **kwargs)   


    
    
    
    
    
    
    
    
    
    
    
    
    