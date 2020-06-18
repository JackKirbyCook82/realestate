# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
import math

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from utilities.strings import uppercase
from utilities.utility import BelowSubsistenceError

from realestate.finance import InsufficientFundError, InsufficientCoverageError, UnsolventLifeStyleError, UnstableLifeStyleError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Investment_Property_Market', 'Personal_Property_Market']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_zscore = lambda x: (x - np.nanmean(x)) / np.nanstd(x)
_threshold = lambda x, z: np.where(x > z, x, np.NaN)
_normalize = lambda x: x / np.nansum(x)
_minmax = lambda x: (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x))
_summation = lambda x: np.nansum(x)


class Investment_Property_Market(object):
    pass


class Personal_Property_Market(object):
    def __init__(self, tenure, *args, households=[], housings=[], rtol=0.01, atol=0.01, maxsteps=250, pricestep=1, relaxstep=10, relaxrate=0.1, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        self.__coveraged = lambda x: np.allclose(x, np.zeros(x.shape), rtol=rtol, atol=atol) 
        self.__households, self.__housings = households, housings
        self.__prices = np.array([[housing.price(tenure) for housing in housings]])
        self.__pricestep = lambda step: pricestep * ((1 - relaxrate) ** math.floor(step / relaxstep))
        self.__maxsteps = maxsteps
        self.__tenure = tenure
        
    def __call__(self, *args, **kwargs): 
        for step in range(self.__maxsteps):
            utilitymatrix = self.utility_matrix(self.__housings, self.__households, *args, **kwargs)
            supplydemandbalances = self.supplydemand_balances(utilitymatrix, *args, **kwargs)
            if self.__coveraged(supplydemandbalances): break
            priceadjustments = self.price_adjustments(supplydemandbalances, *args, **kwargs) * self.__pricestep(step)
            for priceadjustment, housing in zip(priceadjustments, self.__housings): housing(priceadjustment, *args, tenure=self.__tenure, **kwargs) 
            self.__prices = np.concatenate([self.__prices, np.array([[housing.price(self.__tenure) for housing in self.__housings]])], axis=0)
                            
    def utility_matrix(self, housings, households, *args, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        utilitymatrix = np.empty((len(housings), len(households)))
        utilitymatrix[:] = np.NaN
        for i, housing in enumerate(housings):
            for j, household in enumerate(households):
                try: utilitymatrix[i, j] = household(housing, *args, tenure=self.__tenure, **kwargs)
                except InsufficientFundError: pass
                except InsufficientCoverageError: pass
                except UnsolventLifeStyleError: pass
                except UnstableLifeStyleError: pass
                except BelowSubsistenceError: pass
        return utilitymatrix

    def supplydemand_balances(self, utilitymatrix, *args, **kwargs):
        householdcounts = [household.count for household in self.__households]
        housingcounts = [housing.count for housing in self.__housings]    
        supplydemandmatrix = np.apply_along_axis(_normalize, 0, utilitymatrix)
        supplydemandbalances = (np.nansum(supplydemandmatrix * householdcounts, axis=1) - housingcounts) / housingcounts           
        return supplydemandbalances
    
    def price_adjustments(self, supplydemandbalances, *args, **kwargs):
        assert len(self.__housings) == len(supplydemandbalances)
        prices = np.array([housing.sqftprice(self.__tenure, *args, **kwargs) for housing in self.__housings])
        priceadjustments = prices * supplydemandbalances
        return priceadjustments
    
    @keydispatcher
    def table(self, key, *args, **kwargs): raise KeyError(key)

    @table.register('household', 'households')
    def tableHouseholds(self, *args, **kwargs):
        dataframe = pd.concat([household.toSeries(*args, **kwargs) for household in self.__households], axis=1).transpose()
        dataframe.columns = [uppercase(column) for column in dataframe.columns]
        dataframe.index.name = 'Households'
        return dataframe

    @table.register('housing', 'housings')
    def tableHousings(self, *args, **kwargs):
        dataframe = pd.concat([housing.toSeries(*args, **kwargs) for housing in self.__housings], axis=1).transpose()
        dataframe.columns = [uppercase(column) for column in dataframe.columns]
        dataframe.index.name = 'Housing'
        return dataframe
    
    @table.register('price', 'prices')
    def tablePrices(self, *args, tenure, **kwargs):
        dataframe = pd.DataFrame(self.__prices)
        dataframe.columns.name = 'Housing'
        dataframe.index.name = 'Step'
        return dataframe






        
        
        
        
        
        