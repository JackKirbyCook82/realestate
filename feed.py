# -*- coding: utf-8 -*-
"""
Created on Mon Apr 27 2020
@name:   Real Estate Constructor Objects
@author: Jack Kirby Cook

"""

import numpy as np
import pandas as pd
from scipy.linalg import cholesky, eigh
from collections import OrderedDict as ODict

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['MonteCarlo']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


#class Feed(object):
#    
#    
#    @property
#    def histograms(self): return list(self.__histogramIDs.keys())
#    @property
#    def rates(self): return list(self.__rateIDs.keys())    
#    
#    def __init__(self, process, histogramIDs={}, rateIDs={}):
#        self.__histogramIDs = histogramIDs
#        self.__rateIDs = rateIDs
#        self.__calculations = process()
#
#    def getArrayTable(self, tableID, *args, **kwargs): return self.__calculations[tableID](*args, **kwargs)
#    def getHistTable(self, table, *args, date, geography, **kwargs): 
#        return self.getArrayTable(self.__histogramIDs[table], *args, **kwargs).sel(geography=geography, date=date).squeeze('geography').squeeze('date')    
#    def getRateTable(self, table, *args, geography, **kwargs): 
#        return self.getArrayTable(self.__rateIDs[table], *args, **kwargs).sel(geography=geography).squeeze('geography')
#
#    def __call__(self, *args, date, geography, **kwargs):
#        histograms = {table:self.getHistTable(table, *args, date, geography, **kwargs) for table in self.histograms}
#        rates = {table:self.getRateTable(table, *args, date, geography, **kwargs) for table in self.rates}
#        return {**histograms, **rates}
        

class MonteCarlo(object):
    @property
    def name(self): return self.__name
    @property
    def keys(self): return list(self.__histtables.keys())
    
    def __init__(self, name, **histtables):
        self.__name = name
        self.__histtables = ODict([(key, value) for key, value in histtables.items()])
        self.__correlationmatrix = np.zero((len(self), len(self)))
        np.fill_diagonal(self.__correlationmatrix, 1)

    def __call__(self, size, *args, **kwargs):
        samplematrix = self.__samplematrix(size, *args, **kwargs)    
        sampletable = {key:list(values) for key, values in zip(self.keys, samplematrix)}
        return pd.DataFrame({sampletable})               
        
    def __samplematirx(self, size, *args, method='cholesky', **kwargs):
        samplematrix = np.array([table(size) for table in self.__tables.values()]) 
        if method == 'cholesky':
            correlation_matrix = cholesky(self.__correlationmatrix, lower=True)
        elif method == 'eigen':
            evals, evecs = eigh(self.__correlationmatrix)
            correlation_matrix = np.dot(evecs, np.diag(np.sqrt(evals)))
        else: raise ValueError(method)
        return np.dot(correlation_matrix, samplematrix).transpose()    
    
    











    