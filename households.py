# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

from realestate.finance import Financials, UnstableLifeStyleError
from realestate.utility import UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass
class NegativeUtilityError(Exception): pass


def createHouseholdKey(*args, date, age, race, language, education, children, size, financials, utility, **kwargs):
    return (date.index, age, race, language, education, children, size, financials.key, utility.key,)


class Household(ntuple('Household', 'date age race language education children size financials utility')):
    __lifetimes = {'adulthood':15, 'retirement':65, 'death':95}  
    __utility = 'simple'
    __parameters = ('spending', 'crime', 'school', 'quality', 'space', 'proximity', 'community',)
    
    @classmethod
    def customize(cls, *args, **kwargs):
        cls.__lifetimes = kwargs.get('lifetimes', cls.__lifetimes)   
        cls.__utility = kwargs.get('utility', cls.__utility)
        cls.__parameters = kwargs.get('parameters', cls.__parameters)

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
        key = hash(createHouseholdKey(*args, **kwargs))
        try: return cls.__instances[key]
        except KeyError: 
            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
            cls.__instances[key] = newinstance
            return newinstance
    
    def __init__(self, *args, count=1, **kwargs):                    
        try: self.__count = self.__count + count
        except AttributeError: self.__count = count

    def __call__(self, housing, *args, tenure, economy, **kwargs):
        spending = self.evaluate(tenure, housing, *args, **kwargs)
        factor = np.prod(np.array([1+economy.inflationrate(i, units='year') for i in range(economy.date.year, self.date.year)]))
        consumption = spending * factor * economy.purchasingpower   
        if consumption <= 0: raise UnstableLifeStyleError()
        utility = self.utility(*args, housing=housing, household=self, consumption=consumption, **kwargs)
        if utility < 0: raise NegativeUtilityError()
        return utility
    
    @keydispatcher
    def evaluate(self, tenure, housing, *args, **kwargs): raise KeyError(tenure) 
    @evaluate.register('renter')
    def evaluate_renter(self, housing, *args, **kwargs):
        newfinancials = self.financials.sale(*args, **kwargs)    
        housingcost = housing.rentercost
        return newfinancials.consumption - housingcost  
    @evaluate.register('owner')
    def evaluate_owner(self, housing, *args, **kwargs):
        newfinancials = self.financials.sale(*args, **kwargs)
        newfinancials = newfinancials.purchase(housing.purchaseprice, *args, **kwargs)
        housingcost = housing.ownercost + newfinancials.mortgage.payment
        return newfinancials.consumption - housingcost
    
    @property
    def key(self): return hash(createHouseholdKey(**self.todict()))   
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return self.key == other.key    
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    def toSeries(self, *args, **kwargs):
        content = {'count':self.count, 'age':self.age, 'race':self.race, 'education':self.education}
        content.update({'income':self.financials.income, 'consumption':self.financials.consumption, 'netwealth':self.financials.netwealth})
        series = pd.Series(content)
        return series

    @classmethod
    def create(cls, *args, date, household={}, financials={}, economy, **kwargs):
        assert isinstance(household, dict) and isinstance(financials, dict)
        rates = dict(wealthrate=economy.wealthrate(date.year, units='month'), incomerate=economy.incomerate(date.year, units='month'))
        income_horizon = max((cls.__lifetimes['retirement'] - household['age']) * 12, 0)
        consumption_horizon = max((cls.__lifetimes['death'] - household['age']) * 12, 0)   
        financials = Financials.create(income_horizon, consumption_horizon, **financials, **rates)
        utility = UtilityFunction.getfunction(cls.__utility).create(cls.__parameters, **household)
        return cls(*args, date=date, **household, financials=financials, utility=utility, **kwargs)   


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    