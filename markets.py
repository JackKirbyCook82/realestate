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
from utilities.dispatchers import clskey_singledispatcher as keydispatcher

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

percent_delta_price = lambda supply, demand, elasticity: (1 / elasticity) * ((supply / demand) - 1)
percent_price = lambda pdp, step: (pdp * step) + 1 

class ConvergenceError(Exception): pass
class HistoryLengthError(Exception): pass


class Market(ABC):
    @abstractmethod
    def supplys(self, *args, **kwargs): pass
    @abstractmethod
    def demands(self, *args, **kwargs): pass
    @abstractmethod
    def prices(self, *args, **kwargs): pass


class Market_History(object):
    def __bool__(self): return len(self) > 0
    def __len__(self): 
        try: return self.__prices.shape[1] 
        except AttributeError: return 0
    
    @property
    def prices(self): return self.__prices if self else None
    @property
    def demands(self): return self.__demands if self else None
    @property
    def supplys(self): return self.__supplys if self else None

    @property
    def dP(self): return self.prices[:, 1:] - self.prices[:, :-1] if len(self) > 1 else None
    @property
    def dQ(self): return self.demands[:, 1:] - self.demands[:, :-1] if len(self) > 1 else None
    @property
    def dS(self): return self.supplys[:, 1:] - self.supplys[:, :-1] if len(self) > 1 else None
   
    def __init__(self, *args, **kwargs): pass
    def __call__(self, *args, **kwargs): 
        try: supplys, demands, prices = [getattr(kwargs.pop('market'), attr) for attr in ('supplys', 'demands', 'prices',)]
        except KeyError: supplys, demands, prices = [kwargs[key] for key in ('supplys', 'demands', 'prices',)]
        assert all([isinstance(items, np.ndarray) for items in (supplys, demands, prices,)])
        assert supplys.shape == demands.shape == prices.shape
        try: self.__supplys = np.append(self.supplys, np.expand_dims(supplys, axis=1), axis=1)
        except ValueError: self.__supplys = np.expand_dims(supplys, axis=1) 
        try: self.__demands = np.append(self.demands, np.expand_dims(demands, axis=1), axis=1)
        except ValueError: self.__demands = np.expand_dims(demands, axis=1)           
        try: self.__prices = np.append(self.prices, np.expand_dims(prices, axis=1), axis=1)
        except ValueError: self.__prices = np.expand_dims(prices, axis=1)     
    
    def table(self, tabletype, *args, **kwargs): 
        if len(self) <= 1: raise HistoryLengthError()
        else: return self.__table(tabletype, *args, **kwargs) 
        
    @keydispatcher
    def __table(self, tabletype, *args, **kwargs): raise KeyError(tabletype)
    @__table.register('price', 'prices')
    def __tablePrice(self, *args, **kwargs): return self.__dataframe(self.prices, *args, **kwargs) 
    @__table.register('demand', 'demands')
    def __tableDemand(self, *args, **kwargs): return self.__dataframe(self.demands, *args, **kwargs)
    @__table.register('supply', 'supplys')
    def __tableSupply(self, *args, **kwargs): return self.__dataframe(self.supplys, *args, **kwargs)
    @__table.register('elasticity', 'elasticitys')
    def __tableElasticity(self, *args, **kwargs): return self.__dataframe(self.elasticitys, *args, **kwargs) 
    @__table.register('housing')
    def __tableHousing(self, *args, index, **kwargs): 
        data = {'price':self.prices[index, 1:], 'demand':self.demands[index, 1:], 'supply':self.supplys[index, 1:], 'elasticity':self.elasticitys[index, :]}
        return self.__dataframe(data, *args, **kwargs)

    def __dataframe(self, data, *args, period=0, **kwargs):
        assert period >= 0 and isinstance(period, int)
        assert isinstance(data, np.ndarray)
        dataframe = pd.DataFrame(data).transpose()
        if period > 0: dataframe = dataframe.rolling(window=period).mean().dropna(axis=0, how='all')
        return dataframe    


class Personal_Property_Market(Market):
    def __init__(self, tenure, *args, households=[], housings=[], elasticity=-1, stepsize=0.1, maxsteps=100, rtol=0.005, atol=0.01, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        self.__converged = lambda x: np.allclose(x, np.zeros(x.shape), rtol=rtol, atol=atol) 
        self.__households, self.__housings, self.__tenure = households, housings, tenure
        self.__elasticitys = kwargs.get('elasticitys', np.ones(len(housings)) * elasticity)
        self.__maxsteps, self.__stepsize = maxsteps, stepsize   
        try: self.__history = kwargs['history']
        except KeyError: pass
        
    def __call__(self, *args, **kwargs): 
        for step in range(self.__maxsteps):           
            demands = self.demands(*args, **kwargs)
            supplys = self.supplys(*args, **kwargs)
            prices = self.prices(*args, **kwargs)
            try: self.__history(demands=demands, supplys=supplys, prices=prices)
            except AttributeError: pass
            pdp = percent_delta_price(supplys, demands, self.__elasticitys)
            pp = percent_price(pdp, self.__stepsize) 
            newprices = pp * prices
            for newprice, housing in zip(newprices, self.__housings): housing(newprice, *args, tenure=self.__tenure, **kwargs) 
            
    def utilitymatrix(self, *args, **kwargs):
        utilitymatrix = np.empty((len(self.__housings), len(self.__households)))
        deltamatrix = np.empty((len(self.__housings), len(self.__households)))
        utilitymatrix[:] = np.NaN
        deltamatrix[:] = np.NaN
        for i, housing in enumerate(self.__housings):
            for j, household in enumerate(self.__households):
                try: utilitymatrix[i, j], deltamatrix[i, j] = household(housing, *args, tenure=self.__tenure, **kwargs)
                except InsufficientFundError: pass
                except InsufficientCoverageError: pass
                except UnsolventLifeStyleError: pass
                except UnstableLifeStyleError: pass
                except BelowSubsistenceError: pass
        return utilitymatrix, deltamatrix
     
    def supplydemandmatrix(self, *args, **kwargs): 
        utilitymatrix, deltamatrix = self.utilitymatrix(*args, **kwargs)

#       np.apply_along_axis(_normalize, 0, )      
        return
    
    def prices(self, *args, **kwargs): return np.array([housing.price(self.__tenure) for housing in self.__housings])
    def supplys(self, *args, **kwargs): return np.array([housing.count for housing in self.__housings])     
    def demands(self, *args, **kwargs): 
        supplydemandmatrix = self.supplydemandmatrix(*args, **kwargs)
        householdcounts = np.array([household.count for household in self.__households])
        return np.nansum(supplydemandmatrix * householdcounts, axis=1)

    def table(self, *args, **kwargs):
        householdcounts = np.array([household.count for household in self.__households])
        supplydemandmatrix = self.supplydemandmatrix(self, *args, **kwargs) 
        supplydemandmatrix[np.isnan(supplydemandmatrix)] = 0
        dataframe = pd.DataFrame(supplydemandmatrix * householdcounts).transpose().fillna(0)
        dataframe['T'] = dataframe.sum(axis=1)
        dataframe.loc['T'] = dataframe.sum(axis=0)
        dataframe.columns.name = 'Housings'
        dataframe.index.name = 'Households'
        dataframe.name = uppercase(self.__tenure)        
        return dataframe        
    
    

      
    


       


        
        
        
        