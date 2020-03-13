# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Objects
@author: Jack Kirby Cook

"""

import numpy as np
import math

from realestate.participants import Household, Housing
from realestate.finance import InsufficientFundsError, InsufficientCoverageError, UnstableLifeStyleError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Market']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


MARKETFUNCTIONS = {
    'hyperbolic_tangent': lambda a, k, x: a * math.tanh(k * (x - 1))}

_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_monthsteps = {'year': lambda steps: int(steps * 12), 'month': lambda steps: int(steps)}
_monthduration = {'year': lambda duration: int(duration * 12), 'month': lambda duration: int(duration)}

_allnan = lambda x: all([np.isnan(i) for i in x])
_anynan = lambda x: any([np.isnan(i) for i in x])
_allzero = lambda x: all([i == 0 for i in x])
_anyzero = lambda x: any([i == 0 for i in x])

_zscore = lambda x: (x - np.nanmean(x)) / np.nanstd(x)
_threshold = lambda x, z: np.where(x > z, x, np.NaN)
_fill = lambda x: np.ones(len(x)) if _allnan(x) else x
_normalize = lambda x: x / np.nansum(x)
_summation = lambda x: np.nansum(x)


class Market(object):
    def __init__(self, max_market_movement, market_sensitivity, *args, households=[], housings=[], functiontype='hyperbolic_tangent', **kwargs):
        assert all([isinstance(household, Household) for household in _aslist(households)])
        assert all([isinstance(housing, Housing) for housing in _aslist(housings)])
        self.__households = _aslist(households)
        self.__housing = _aslist(housings)
        self.__function = MARKETFUNCTIONS[functiontype]
        self.__maxMarketMovement = max_market_movement
        self.__marketSensitivity = market_sensitivity

    @property
    def coefficents(self): return (self.__maxMarketMovement, self.__marketSensitivity)
    @property
    def households(self): return self.__households
    @property
    def housing(self): return self.__housing

    def demand_supply_ratios(self, *args, horizon_years, horizon_wealth_multiple, **kwargs):
        owner_utility_matrix = self.utility_matrix('owner', horizon_years, horizon_wealth_multiple, *args, **kwargs)
        renter_utility_matrix = self.utility_matrix('renter', horizon_years, horizon_wealth_multiple, *args, **kwargs)        
        total_utility_matrix = np.concatenate((owner_utility_matrix, renter_utility_matrix), axis=0)      
        owner_demand_matrix, renter_demand_matrix = self.demand_matrix(total_utility_matrix, *args, **kwargs)      
        owner_supply_matrix, renter_supply_matrix = self.supply_matrix(*args, **kwargs)
        owner_demand_supply_ratios = owner_demand_matrix / owner_supply_matrix
        renter_demand_supply_ratios = renter_demand_matrix / renter_supply_matrix
        return owner_demand_supply_ratios, renter_demand_supply_ratios

    def utility_matrix(self, tenure, horizon_years, horizon_wealth_multiple, *args, **kwargs):
        utilitymatrix = np.empty((len(self.__housing), len(self.__households)))
        for i, housing in enumerate(self.__housing):
            for j, household in enumerate(self.__households):
                try: utilitymatrix[i, j] = household.utility(housing, tenure, horizon_years, horizon_wealth_multiple, *args, **kwargs)
                except InsufficientFundsError: pass
                except InsufficientCoverageError: pass
                except UnstableLifeStyleError: pass
        return utilitymatrix

    def supply_matrix(self, *args, **kwargs):
        owner_supply_matrix = np.array([housing.ownercount for housing in self.__housing])
        renter_supply_matrix = np.array([housing.rentercount for housing in self.__housing])       
        return owner_supply_matrix, renter_supply_matrix

    def demand_matrix(self, utility_matrix, *args, demand_threshold, **kwargs):
        utility_matrix = np.apply_along_axis(_zscore, 0, utility_matrix)
        utility_matrix = np.apply_along_axis(_threshold, 0, utility_matrix, demand_threshold)
        utility_matrix = np.apply_along_axis(_fill, 0, utility_matrix)
        utility_matrix = np.apply_along_axis(_normalize, 0, utility_matrix)
        owner_utility_matrix, renter_utility_matrix = np.split(utility_matrix, 2, axis=0)
        owner_demand_matrix = np.apply_along_axis(_summation, 1, owner_utility_matrix)
        renter_demand_matrix = np.apply_along_axis(_summation, 1, renter_utility_matrix)
        return owner_demand_matrix, renter_demand_matrix
    
    def __call__(self, duration, *args, basis='monthly', **kwargs): 
        duration = min(_monthduration[basis](duration), self.duration)
        ownerDSR, renterDSR = self.demand_supply_ratios(*args, **kwargs)
        priceRates, rentRates = self.__function(*self.coefficents, ownerDSR), self.__function(*self.coefficents, renterDSR)
        for index, household in enumerate(self.__households): 
            self.__households[index] = household(duration, *args, basis='monthly', **kwargs)
        for index, housing in enumerate(self.__housing):
            self.__housing[index] = housing(duration, *args, basis='monthly', pricerate=priceRates[index], rentrate=rentRates[index], **kwargs)            
        return self
        
        





