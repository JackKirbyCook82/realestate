# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd

from utilities.strings import uppercase
from utilities.dispatchers import clskey_singledispatcher as keydispatcher

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Personal_Property_Market', 'Market_History']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_multiply = lambda x, y: x * y
_divide = lambda x, y: x / y
_normalize = lambda x: x / np.nansum(x)
_diffnormalize = lambda x: (np.nansum(x) - x) / (np.nansum(x)**2)
_minmax = lambda x: (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x))
_summation = lambda x: np.nansum(x)
_logdiff = lambda x, xmin, xmax: np.log10(np.clip(x, 0.1, 10))
_meansqerr = lambda x, y: np.round((np.square(x - y)).mean() ** 0.5, 3)
_maxsqerr = lambda x, y: np.round(np.max(np.square(x - y)) ** 0.5, 3)


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
        if len(self) <= 1: raise ValueError()
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


class Personal_Property_Market(object):
    @property
    def i(self): return len(self.__housings)
    @property
    def j(self): return len(self.__households)
    @property
    def k(self): return len(self.__housings)
    @property
    def shape(self): return (self.j, self.i, self.k)
    
    def __init__(self, tenure, *args, households=[], housings=[], stepsize=0.1, maxsteps=500, rtol=0.005, atol=0.01, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        assert tenure == 'renter' or tenure == 'owner'
        assert stepsize < 1
        self.__converged = lambda x: np.allclose(x, np.zeros(x.shape), rtol=rtol, atol=atol) 
        self.__households, self.__housings, self.__tenure = households, housings, tenure
        self.__maxsteps, self.__stepsize = maxsteps, stepsize  
        try: self.__history = kwargs['history']
        except KeyError: pass
 
    def __call__(self, *args, **kwargs): 
        for step in range(self.__maxsteps):           
            supplys, demands, prices = self.execute(*args, **kwargs)
            try: self.__history(demands=demands, supplys=supplys, prices=prices)
            except AttributeError: pass
            meansqerr, maxsqerr = _meansqerr(demands, supplys), _maxsqerr(demands, supplys)
            print('Market Converging(step={}, avgerror={}, maxerror={})'.format(step, meansqerr, maxsqerr))
            if self.__converged(demands - supplys): break
            dPP = np.log10(np.clip(demands / supplys, 0.1, 10)) * self.__stepsize
            newprices = prices * (1 + dPP)
            for price, housing in zip(newprices, self.__housings): housing(price, *args, tenure=self.__tenure, **kwargs)         
 
    def execute(self, *args, **kwargs): 
        uMatrix, _ = self.evaluate(*args, **kwargs)
        prices = self.prices(*args, **kwargs)
        supplys = self.supplys(*args, **kwargs)
        demands = self.demands(*args, uMatrix=uMatrix, **kwargs)
        return supplys, demands, prices

    def evaluate(self, *args, **kwargs):
        uMatrix = np.empty((len(self.__housings), len(self.__households),)) 
        duMatrix = np.empty((len(self.__housings), len(self.__households),))
        uMatrix[:], duMatrix[:] = np.NaN, np.NaN
        for i, housing in enumerate(self.__housings):
            for j, household in enumerate(self.__households):
                uMatrix[i, j], duMatrix[i, j] = household(housing, *args, tenure=self.__tenure, filtration='consumption', **kwargs)
        return uMatrix, duMatrix    
    
    def prices(self, *args, **kwargs): return np.array([housing.price(self.__tenure) for housing in self.__housings])
    def supplys(self, *args, **kwargs): return np.array([housing.count for housing in self.__housings])

    def demands(self, *args, uMatrix, **kwargs): 
        weights = np.array([household.count for household in self.__households])
        uMatrix = np.apply_along_axis(_normalize, 0, uMatrix)
        demands = np.apply_along_axis(_summation, 1, uMatrix * weights)  
        return demands

    def elasticitys(self, *args, uMatrix, duMatrix, **kwargs):           
        cpMatrix = self.cpMatrix(*args, **kwargs)
        ucMatrix = self.ucMatrix(*args, duMatrix=duMatrix, **kwargs)
        zuMatrix = self.zuMatrix(*args, uMatrix=uMatrix, **kwargs)
        dzMatrix = self.dzMatrix(self, *args, **kwargs)        
        dpMatrix = dzMatrix * zuMatrix * ucMatrix * cpMatrix       
        elasticitys = np.apply_along_axis(_summation, 0, dpMatrix)
        elasticitys = np.apply_along_axis(_summation, 0, dpMatrix)          
        return elasticitys

    def cpMatrix(self, *args, economy, date, **kwargs):
        cpi = np.prod(np.array([1+economy.inflationrate(i, units='year') for i in range(economy.date.year, date.year)]))        
        cpMatrix = np.ones(self.shape) * cpi
        assert cpMatrix.shape == self.shape
        return cpMatrix

    def ucMatrix(self, *args, duMatrix, **kwargs):
        ucMatrix = np.broadcast_to(np.expand_dims(duMatrix.transpose(), axis=2), self.shape)
        assert ucMatrix.shape == self.shape
        return ucMatrix

    def zuMatrix(self, *args, uMatrix, **kwargs):
        eye = np.broadcast_to(np.expand_dims(np.eye(self.i), axis=0), self.shape)
        zero = np.where(eye == 1, 0, 1)
        iij = np.broadcast_to(np.expand_dims(uMatrix.transpose(), axis=2), self.shape)
        off = (iij * eye) - iij
        on = np.broadcast_to(np.expand_dims(np.apply_along_axis(_summation, 2, iij * zero), axis=2), self.shape) * eye
        zuMatrix = np.apply_along_axis(_divide, 0, off + on, np.apply_along_axis(_summation, 0, uMatrix) ** 2)
        assert zuMatrix.shape == self.shape
        return zuMatrix
    
    def dzMatrix(self, *args, **kwargs):
        weights = np.array([household.count for household in self.__households])
        dzMatrix = np.apply_along_axis(_multiply, 0, np.ones(self.shape), weights)
        assert dzMatrix.shape == self.shape
        return dzMatrix
                
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
    
    

      
    


       


        
        
        
        