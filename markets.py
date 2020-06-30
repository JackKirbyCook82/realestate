# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd

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
_avgerror = lambda x: np.round(np.mean(x**2)**0.5, 3) 
_maxerror = lambda x: np.round(np.max(x**2)**0.5, 3)


class ConvergenceError(Exception): pass


class Personal_Property_Market(object):
    def __init__(self, tenure, *args, households=[], housings=[], rtol=0.002, atol=0.005, maxsteps=500, stepsize=0.1, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        self.__converged = lambda x: np.allclose(x, np.zeros(x.shape), rtol=rtol, atol=atol) 
        self.__households, self.__housings = households, housings
        self.__prices = np.expand_dims(np.array([housing.price(tenure) for housing in housings]), axis=1)
        self.__maxsteps, self.__stepsize = maxsteps, stepsize
        self.__tenure = tenure
        
    def __call__(self, *args, **kwargs): 
        for step in range(self.__maxsteps):           
            utilitymatrix = self.utility_matrix(self.__housings, self.__households, *args, **kwargs)
            supplydemandmatrix = self.supplydemand_matrix(utilitymatrix, *args, **kwargs)
            supplydemandbalances = self.supplydemand_balances(supplydemandmatrix, *args, **kwargs)
            errorbalances = supplydemandbalances - 1
            if self.__converged(errorbalances): break
            else: print('Market Coverging: Step={}, AvgError={}, MaxError={}'.format(step+1, _avgerror(errorbalances), _maxerror(errorbalances))) 
            netpriceadjustments = self.price_adjustments(supplydemandbalances, *args, **kwargs) * self.__stepsize
            for netpriceadjustment, housing in zip(netpriceadjustments, self.__housings): housing(netpriceadjustment, *args, tenure=self.__tenure, **kwargs) 
            newprices = np.expand_dims(np.array([housing.price(self.__tenure) for housing in self.__housings]), axis=1)
            self.__prices = np.append(self.__prices, newprices, axis=1)
        if not self.__converged(errorbalances): raise ConvergenceError(supplydemandbalances)
                 
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
        supplydemandbalances = np.nansum(supplydemandmatrix * householdcounts, axis=1) / housingcounts           
        return supplydemandbalances
    
    def price_adjustments(self, *args, **kwargs):
        try: supplydemandbalances = args.pop(0)
        except: supplydemandbalances = self.supplydemand_balances(*args, **kwargs)        
        assert len(self.__housings) == len(supplydemandbalances)
        logsupplydemandbalances = np.log10(np.clip(supplydemandbalances, 0.1, 10)) 
        prices = np.array([housing.price(self.__tenure) for housing in self.__housings])
        priceadjustments = prices * logsupplydemandbalances
        return priceadjustments
    
    def table(self, *args, **kwargs):
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

    def convergence(self, period=0):
        assert period >= 0 and isinstance(period, int)
        dataframe = pd.DataFrame(self.__prices).transpose()
        if period > 0: dataframe = dataframe.rolling(window=period).mean().dropna(axis=0, how='all')
        dataframe.columns.name = 'Housings'
        dataframe.index.name = 'Step'
        dataframe.name = uppercase(self.__tenure)
        return dataframe        


        
        
        
        