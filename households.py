# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housholds Objects
@author: Jack Kirby Cook

"""

import pandas as pd
import numpy as np
from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from utilities.strings import uppercase
from utilities.utility import NumericalError

from realestate.finance import Financials, UnstableLifeStyleError, NegativeConsumptionError, InsufficientFundsError, InsufficientCoverageError
from realestate.utility import Household_UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class PrematureHouseholderError(Exception): pass
class DeceasedHouseholderError(Exception): pass


def createHouseholdKey(*args, date, age, parameters, financials, utility, **kwargs):
    parameters = [hash((key, hash(value),)) for key, value in parameters.items()]
    return (hash(date), hash(age), *parameters, hash(financials.key), hash(utility.key),)


class Household(ntuple('Household', 'date age parameters financials utility')):
    __lifetimes = {'adulthood':15, 'retirement':65, 'death':95}  
    __parameters = tuple()

    @classmethod
    def clear(cls): cls.__instances = {}    
    @classmethod
    def customize(cls, *args, **kwargs):
        cls.clear()
        cls.__parameters = kwargs.get('parameters', cls.__parameters)
        cls.__lifetimes = kwargs.get('lifetimes', cls.__lifetimes)   

    def __repr__(self): 
        content = {'date':repr(self.date), 'age':repr(self.age), 'utility':repr(self.utility), 'financials':repr(self.financials)}
        content.update({key:repr(value) for key, value in self.parameters.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    __instances = {}       
    @property
    def count(self): return self.__count    
    def __new__(cls, *args, date, age, parameters, financials, utility, **kwargs):
        if age < cls.__lifetimes['adulthood']: raise PrematureHouseholderError()
        if age > cls.__lifetimes['death']: raise DeceasedHouseholderError()              
        key = hash(createHouseholdKey(*args, date=date, age=age, parameters=parameters, financials=financials, utility=utility, **kwargs))
        try: return cls.__instances[key]
        except KeyError: 
            parameters = {parameter:parameters[parameter] for parameter in cls.__parameters}
            newinstance = super().__new__(cls, date=date, age=age, parameters=parameters, financials=financials, utility=utility)
            cls.__instances[key] = newinstance
            return newinstance
    
    def __init__(self, *args, count=1, **kwargs):                    
        try: self.__count = self.__count + count
        except AttributeError: self.__count = count
     
    def __call__(self, housing, *args, tenure, filtration, **kwargs):
        try: spending = self.spending(tenure, housing, *args, **kwargs)
        except (UnstableLifeStyleError, NegativeConsumptionError, InsufficientFundsError, InsufficientCoverageError): return np.NaN, np.NaN
        try: 
            utility = self.utility(*args, housing=housing, household=self, spending=spending, **kwargs)
            derivative = self.utility.derivative(filtration, *args, housing=housing, household=self, spending=spending, **kwargs)
        except NumericalError: return np.NaN, np.NaN
        return utility, derivative       
     
    @keydispatcher
    def spending(self, tenure, housing, *args, **kwargs): raise KeyError(tenure) 
    @spending.register('renter')
    def spending_renter(self, housing, *args, **kwargs):
        newfinancials = self.financials.sale(*args, **kwargs)    
        housingcost = housing.rentercost
        return newfinancials.consumption - housingcost  
    @spending.register('owner')
    def spending_owner(self, housing, *args, **kwargs):
        newfinancials = self.financials.sale(*args, **kwargs)
        newfinancials = newfinancials.purchase(housing.purchaseprice, *args, **kwargs)
        housingcost = housing.ownercost + newfinancials.mortgage.payment
        return newfinancials.consumption - housingcost
    
    @property
    def key(self): return createHouseholdKey(**self.todict())   
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return self.key == other.key    
    
    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if not isinstance(item, str): return super().__getitem__(item)
        else: return getattr(self, item)
    def __getattr__(self, attr):
        try: return self.parameters[attr]
        except KeyError: raise AttributeError(attr)

    def toSeries(self):
        content = {'count':self.count, 'age':self.age, **{key:value for key, value in self.parameters.items()}}
        content.update({'income':self.financials.income, 'consumption':self.financials.consumption, 'netwealth':self.financials.netwealth})
        series = pd.Series(content)
        return series

    @classmethod
    def table(cls):
        dataframe = pd.concat([household.toSeries() for household in cls.__instances.values()], axis=1).transpose()
        dataframe.columns = [uppercase(column) for column in dataframe.columns]
        dataframe.index.name = 'Households'
        return dataframe

    @classmethod
    def create(cls, *args, date, age, household={}, financials={}, economy, **kwargs):
        assert isinstance(household, dict) and isinstance(financials, dict)
        income_horizon = max((cls.__lifetimes['retirement'] - age) * 12, 0)
        consumption_horizon = max((cls.__lifetimes['death'] - age) * 12, 0)   
        parameters = {item:household.pop(item) for item in cls.__parameters}
        financials = Financials.create(income_horizon, consumption_horizon, date=date, age=age, economy=economy, **financials)
        utility = Household_UtilityFunction.create(**household)
        return cls(*args, date=date, age=age, parameters=parameters, financials=financials, utility=utility, **household, **kwargs)   


    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    