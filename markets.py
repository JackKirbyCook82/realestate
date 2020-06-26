# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
import math

from utilities.strings import uppercase
from utilities.utility import BelowSubsistenceError

from realestate.finance import InsufficientFundError, InsufficientCoverageError, UnsolventLifeStyleError, UnstableLifeStyleError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Personal_Property_Market']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_zscore = lambda x: (x - np.nanmean(x)) / np.nanstd(x)
_threshold = lambda x, z: np.where(x > z, x, np.NaN)
_normalize = lambda x: x / np.nansum(x)
_minmax = lambda x: (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x))
_summation = lambda x: np.nansum(x)


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
            supplydemandmatrix = self.supplydemand_matrix(utilitymatrix, *args, **kwargs)
            supplydemandbalances = self.supplydemand_balances(supplydemandmatrix, *args, **kwargs)
            if self.__coveraged(supplydemandbalances): break
            priceadjustments = self.price_adjustments(supplydemandbalances, *args, **kwargs) * self.__pricestep(step)
            for priceadjustment, housing in zip(priceadjustments, self.__housings): housing(priceadjustment, *args, tenure=self.__tenure, **kwargs) 
            self.__prices = np.concatenate([self.__prices, np.array([[housing.price(self.__tenure) for housing in self.__housings]])], axis=0)
                 
    def utility_matrix(self, *args, **kwargs):
        try: housings, households = args.pop(0), args.pop(1)
        except: housings, households = self.__housings, self.__households
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

    def supplydemand_matrix(self, *args, **kwargs):
        try: utilitymatrix = args.pop(0)
        except: utilitymatrix = self.utility_matrix(*args, **kwargs)
        supplydemandmatrix = np.apply_along_axis(_normalize, 0, utilitymatrix)
        return supplydemandmatrix
        
    def supplydemand_balances(self, *args, **kwargs):
        try: supplydemandmatrix = args.pop(0)
        except: supplydemandmatrix = self.supplydemand_matrix(*args, **kwargs)
        householdcounts = np.array([household.count for household in self.__households])
        housingcounts = np.array([housing.count for housing in self.__housings]) 
        supplydemandbalances = (np.nansum(supplydemandmatrix * householdcounts, axis=1) - housingcounts) / housingcounts           
        return supplydemandbalances
    
    def price_adjustments(self, *args, **kwargs):
        try: supplydemandbalances = args.pop(0)
        except: supplydemandbalances = self.supplydemand_balances(*args, **kwargs)        
        assert len(self.__housings) == len(supplydemandbalances)
        supplydemandbalances = np.clip(supplydemandbalances, -1, 1)
        prices = np.array([housing.price(self.__tenure) for housing in self.__housings])
        priceadjustments = prices * supplydemandbalances
        return priceadjustments

    def supplydemandTable(self, *args, **kwargs):
        householdcounts = np.array([household.count for household in self.__households])
        supplydemandmatrix = self.supplydemand_matrix(self, *args, **kwargs) 
        supplydemandmatrix[np.isnan(supplydemandmatrix)] = 0
        dataframe = pd.DataFrame(supplydemandmatrix * householdcounts).transpose().fillna(0)
        dataframe['T'] = dataframe.sum(axis=1)
        dataframe.loc['T'] = dataframe.sum(axis=0)
        dataframe.columns.name = 'Housings'
        dataframe.index.name = 'Households'
        dataframe.name = uppercase(self.__tenure)        
        return dataframe
        
    def convergenceTable(self, *args, **kwargs):
        dataframe = pd.DataFrame(self.__prices)
        dataframe.columns.name = 'Housings'
        dataframe.index.name = 'Step'
        dataframe.name = uppercase(self.__tenure)
        return dataframe

        
    




        
        
        
        
        
        