# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from abc import ABC, abstractmethod

from utilities.strings import uppercase
from utilities.utility import BelowSubsistenceError

from realestate.finance import InsufficientFundError, InsufficientCoverageError, UnsolventLifeStyleError, UnstableLifeStyleError

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Personal_Property_Market', 'Market_History']
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


#    def price_adjustments(self, *args, **kwargs):
#        try: supplydemandbalances = args.pop(0)
#        except: supplydemandbalances = self.supplydemand_balances(*args, **kwargs)        
#        assert len(self.__housings) == len(supplydemandbalances)
#        logsupplydemandbalances = np.log10(np.clip(supplydemandbalances, 0.1, 10)) 
#        prices = np.array([housing.price(self.__tenure) for housing in self.__housings])
#        priceadjustments = prices * logsupplydemandbalances
#        return priceadjustments


def pricedelta_calculation(supply, demand, price, elasticity):
    assert all([isinstance(item, np.ndarray) for item in (supply, demand, price, elasticity,)])
    assert supply.shape == demand.shape == price.shape == elasticity.shape
    dp = np.divide(1, elasticity) * (np.divide(supply, demand) - 1) * price
    return dp

def elasticity_calculation(supply, demand, price, dprice):
    e = ((supply - demand) / demand) / (dprice / price)
    return e


class ConvergenceError(Exception): pass


class Market(ABC):
    @abstractmethod
    def supplys(self, *args, **kwargs): pass
    @abstractmethod
    def demands(self, *args, **kwargs): pass
    @abstractmethod
    def prices(self, *args, **kwargs): pass
    @abstractmethod
    def elasticitys(self, *args, **kwargs): pass


class Market_History(object):
    @property
    def prices(self): return self.__prices
    @property
    def demands(self): return self.__demands
    @property
    def supplys(self): return self.__supplys
    @property
    def elasticitys(self): return self.__elasticitys
    
    def __init__(self, prices, supplys, demands, elasticitys):
        assert len(prices) == len(supplys) == len(demands)
        self.__prices = np.expand_dims(prices, axis=1)
        self.__demands = np.expand_dims(demands, axis=1)        
        self.__supplys = np.expand_dims(supplys, axis=1)
        self.__elasticitys = np.expand_dims(elasticitys, axis=1)

    def __call__(self, *args, **kwargs):
        try: supplys, demands, prices, elasticitys = [getattr(kwargs.pop('market'), attr) for attr in ('supplys', 'demands', 'prices', 'elasticitys',)]
        except KeyError: supplys, demands, prices, elasticitys = [kwargs[key] for key in ('supplys', 'demands', 'prices', 'elasticitys',)]
        self.__update(supplys, demands, prices, elasticitys)            
        
    def __update(self, supplys, demands, prices, elasticitys):
        self.__supplys = np.append(self.supplys, np.expand_dims(supplys, axis=1), axis=1)
        self.__demands = np.append(self.demands, np.expand_dims(demands, axis=1), axis=1)
        self.__prices = np.append(self.prices, np.expand_dims(prices, axis=1), axis=1)
        self.__elasticitys = np.append(self.elasticitys, np.expand_dims(elasticitys, axis=1), axis=1)

    @classmethod
    def fromMarket(cls, market, *args, **kwargs):
        assert isinstance(market, Market)
        supplys = market.supplybalances(*args, **kwargs)
        demands = market.demandbalances(*args, **kwargs)
        prices = market.pricebalances(*args, **kwargs)
        elasticitys = market.elasticitybalances(*args, **kwargs)
        return cls(prices, supplys, demands, elasticitys)
    
    def table(self, period=0):
        assert period >= 0 and isinstance(period, int)
        dataframe = pd.DataFrame(self.__prices).transpose()
        if period > 0: dataframe = dataframe.rolling(window=period).mean().dropna(axis=0, how='all')
        dataframe.columns.name = 'Housings'
        dataframe.index.name = 'Step'
        dataframe.name = uppercase(self.__tenure)
        return dataframe    


class Personal_Property_Market(Market):
    def __init__(self, tenure, *args, households=[], housings=[], rtol=0.005, atol=0.01, stepsize=0.1, maxsteps=250, elasticity=1, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        self.__converged = lambda x: np.allclose(x, np.zeros(x.shape), rtol=rtol, atol=atol) 
        self.__households, self.__housings, self.__tenure = households, housings, tenure
        self.__elasticitys = np.ones(len(self.__housings)) * elasticity
        self.__maxsteps, self.__stepsize = maxsteps, stepsize
 
    def __call__(self, *args, **kwargs): 
        for step in range(self.__maxsteps):           
            supplys, demands = self.supplys(*args, **kwargs), self.demands(*args, **kwargs)
            errors = (demands / supplys) - 1
            if self.__converged(errors): break
            else: print('Market Coverging: Step={}, AvgError={}, MaxError={}'.format(step+1, _avgerror(errors), _maxerror(errors))) 
            prices = self.prices(*args, **kwargs)
            elasticitys = self.elasticitys(*args, **kwargs)
            pricedifferentials = pricedelta_calculation(supplys, demands, prices, elasticitys)
            newprices = prices + pricedifferentials
            newelasticitys = elasticity_calculation(supplys, demands, newprices, pricedifferentials)
            for newprice, housing in zip(newprices, self.__housings): housing(newprice, *args, tenure=self.__tenure, **kwargs) 
            self.__elasticitys = newelasticitys
        if not self.__converged(errors): raise ConvergenceError()

    def supplydemandmatrix(self, *args, **kwargs): return np.apply_along_axis(_normalize, 0, self.utilitymatrix(*args, **kwargs))              
    def utilitymatrix(self, *args, **kwargs):
        utilitymatrix = np.empty((len(self.__housings), len(self.__households)))
        utilitymatrix[:] = np.NaN
        for i, housing in enumerate(self.__housings):
            for j, household in enumerate(self.__households):
                try: utilitymatrix[i, j] = household(housing, *args, tenure=self.__tenure, **kwargs)
                except InsufficientFundError: pass
                except InsufficientCoverageError: pass
                except UnsolventLifeStyleError: pass
                except UnstableLifeStyleError: pass
                except BelowSubsistenceError: pass
        return utilitymatrix
       
    def prices(self, *args, **kwargs): return np.array([housing.price(self.__tenure) for housing in self.__housings])
    def elasticitys(self, *args, **kwargs): return self.__elasticitys
    def supplys(self, *args, **kwargs): return np.array([housing.count for housing in self.__housings])     
    def demands(self, *args, **kwargs): 
        supplydemandmatrix = self.supplydemandmatrix(*args, **kwargs)
        householdcounts = np.array([household.count for household in self.__households])
        return np.nansum(supplydemandmatrix * householdcounts, axis=1)

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
    
    

      
    


       


        
        
        
        