# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd

from utilities.dispatchers import clskey_singledispatcher as keydispatcher

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
    def __init__(self, tenure, *args, households=[], housings=[], rtol=0.001, atol=0.001, maxcycles=15, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        self.__households, self.__housings = households, housings
        self.__coveraged = lambda x: np.allclose(x, np.ones(x.shape), rtol=rtol, atol=atol) 
        self.__tenure = tenure
        self.__maxcycles = maxcycles

    def equilibrium(self, *args, **kwargs): 
        for cycle in range(self.__maxcycles):
            utilitymatrix = self.utility_matrix(self.__housings, self.__households, *args, **kwargs)
            supplydemandmatrix = self.supplydemand_matrix(utilitymatrix, *args, **kwargs)
            supplydemandratios = self.supplydemand_ratios(supplydemandmatrix, *args, **kwargs)
            self.update(supplydemandratios, *args, **kwargs)    
            if self.__coveraged(supplydemandratios): break

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
        return utilitymatrix

    def supplydemand_matrix(self, utilitymatrix, *args, **kwargs):
        supplydemandmatrix = np.apply_along_axis(_normalize, 0, utilitymatrix)
        return supplydemandmatrix
             
    def supplydemand_ratios(self, supplydemandmatrix, *args, **kwargs):
        householdcounts = [household.count for household in self.__households]
        housingcounts = [housing.count for housing in self.__housings]    
        supplydemandmatrix = supplydemandmatrix * householdcounts
        supplydemandratios = np.nansum(supplydemandmatrix, axis=1) / housingcounts           
        return supplydemandratios
    
    def update(self, supplydemandratios, *args, **kwargs):
        assert len(supplydemandratios) == len(self.__housings)
        for supplydemandratio, housing in zip(supplydemandratios, self.__housings):
            housing(supplydemandratio, *args, tenure=self.__tenure, **kwargs)
        
    @keydispatcher
    def table(self, key, *args, **kwargs): raise KeyError(key)
    @table.register('household', 'households')
    def tableHouseholds(self, *args, **kwargs):
        return pd.concat([household.toSeries(*args, **kwargs) for household in self.__households], axis=1).transpose()
    @table.register('housing', 'housings')
    def tableHousings(self, *args, **kwargs):
        return pd.concat([housing.toSeries(*args, **kwargs) for housing in self.__housings], axis=1).transpose()
        













        
        
        
        
        
        