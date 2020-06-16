# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np

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
    def __init__(self, tenure, *args, households=[], housings=[], **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        self.__households, self.__housings = households, housings
        self.__tenure = tenure

    def __call__(self, *args, **kwargs):
        utilitymatrix = self.utility_matrix(*args, **kwargs)
        supplydemandmatrix = self.supplydemand_matrix(utilitymatrix, *args, **kwargs)
        supplydemandratios = self.supplydemand_ratios(supplydemandmatrix, *args, **kwargs)
        self.__housings = self.update(supplydemandratios)

    def utility_matrix(self, *args, **kwargs):
        utilitymatrix = np.empty((len(self.__housings), len(self.__households)))
        utilitymatrix[:] = np.NaN
        for i, housing in enumerate(self.__housings):
            for j, household in enumerate(self.__households):
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
        housings = []
        assert len(supplydemandratios) == len(self.__housings)
        for supplydemandratio, housing in zip(supplydemandratios, self.__housings):
            housings.append(housing(supplydemandratio, *args, tenure=self.__tenure, **kwargs))
        return housing
        






        
        
        
        
        
        
        
        
        
        
        
        
        
        