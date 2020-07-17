# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd

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
_window = lambda x, n, i: x[i:i+n]
_void = lambda n: np.ones(n-1) * np.NaN
_sma = lambda x, n: np.concatenate([_void(n), np.convolve(x, np.ones(n)/n, 'valid')], axis=0)
_mmax = lambda x, n: np.concatenate([_void(n), np.array([np.amax(_window(x, n, i)) for i in np.arange(len(x)-n+1)])])
_mmin = lambda x, n: np.concatenate([_void(n), np.array([np.amin(_window(x, n, i)) for i in np.arange(len(x)-n+1)])])


class Market_History(object):
    __moving = {'SMA{}':_sma, 'MAX{}':_mmax, 'MIN{}':_mmin}
 
    def __len__(self): return len(self.__data) if self else 0
    def __bool__(self): return hasattr(self, '__data')
    def __init__(self, datakey): self.__datakey = datakey
    def __call__(self, data):
        try: self.__data = np.append(self.__data, np.expand_dims(data, axis=1), axis=1)
        except AttributeError: self.__data = np.expand_dims(data, axis=1)     

    def sma(self, period=1): return np.apply_along_axis(_sma, 1, self.__data) if len(self) >= period else _void(len(self))
    def mmax(self, period=1): return np.apply_along_axis(_mmax, 1, self.__data) if len(self) >= period else _void(len(self))
    def mmin(self, period=1): return np.apply_along_axis(_mmin, 1, self.__data) if len(self) >= period else _void(len(self))

    def __getitem__(self, index):
        def wrapper(period=1):
            assert isinstance(period, int) and period >= 1
            columns = [self.__datakey, 'SMA{}'.format(period), 'MAX{}'.format(period), 'MIN{}'.format(period)]
            data = np.array([self.__data[index, :], _sma(self.__data[index, :], period), _mmax(self.__data[index, :], period), _mmin(self.__data[index, :], period)])
            dataframe = pd.DataFrame(data.transpose(), columns=columns)
            return dataframe
        return wrapper

    def table(self, period=1):
        assert isinstance(period, int) and period >= 1
        dataframe = pd.DataFrame(self.__data.transpose())
        if period > 0: dataframe = dataframe.rolling(window=period).mean().dropna(axis=1, how='all')
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
        try: self.__prices = kwargs['history']['prices']
        except KeyError: pass
        try: self.__demands = kwargs['history']['demands']
        except KeyError: pass
        try: self.__supplys = kwargs['history']['supplys']
        except KeyError: pass
    
    def __call__(self, *args, **kwargs): 
        for step in range(self.__maxsteps):           
            supplys, demands, prices = self.execute(*args, **kwargs)
            self.__update(*args, supplys=supplys, demands=demands, prices=prices, **kwargs)
            meansqerr, maxsqerr = _meansqerr(demands, supplys), _maxsqerr(demands, supplys)
            print('Market Converging(step={}, avgerror={}, maxerror={})'.format(step, meansqerr, maxsqerr))
            if self.__converged(demands - supplys): break
            dPP = np.log10(np.clip(demands / supplys, 0.1, 10)) * self.__stepsize
            newprices = prices * (1 + dPP)
            for price, housing in zip(newprices, self.__housings): housing(price, *args, tenure=self.__tenure, **kwargs)         
 
    def __update(self, *args, **kwargs):
        try: self.__prices(kwargs['prices'])
        except (AttributeError, KeyError): pass
        try: self.__demands(kwargs['demands'])
        except (AttributeError, KeyError): pass
        try: self.__supplys(kwargs['supplys'])
        except (AttributeError, KeyError): pass       
    
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
                

       


        
        
        
        