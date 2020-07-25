# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Utility Objects
@author: Jack Kirby Cook

"""

import numpy as np

from utilities.dictionarys import CallSliceOrderedDict as CSODict
from utilities.utility import UtilityIndex, UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Habitation_UtilityFunction', 'Household_UtilityFunction']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]
_inverse = lambda items: np.array(items).astype('float64')**-1
_normalize = lambda items: np.array(items) / np.sum(np.array(items))


@UtilityFunction.register('habitation', 'ces', parameters=('location', 'quality', 'space',), coefficents=('amplitude', 'diminishrate', 'elasticity',))
class Habitation_UtilityFunction: 
    @classmethod
    def create(cls, *args, **kwargs): 
        weights = {'location':1, 'quality':1, 'space':1}
        coefficents = {'amplitude':1, 'diminishrate':1, 'elasticity':0.5}
        return cls(*args, weights=weights, subsistences={}, **coefficents, **kwargs)    
    
    def execute(self, *args, housing, **kwargs):
        return {'location':housing.location, 'quality':housing.quality, 'space':housing.space}
        
    
@UtilityFunction.register('household', 'cobbdouglas', parameters=('habitation', 'consumption',), coefficents=('amplitude', 'diminishrate',))
class Household_UtilityFunction:
    @classmethod
    def create(cls, *args, **kwargs): 
        functions = {'habitabtion':Habitation_UtilityFunction.create(*args, **kwargs)}
        weights = {'habitation':0.3, 'consumption':1 - 0.3}
        coefficents = {'amplitude':1, 'diminishrate':1}
        return cls(*args, subsistences={}, weights=weights, functions=functions, **coefficents, **kwargs)  

    def execute(self, *args, spending, habitation, economy, date, **kwargs):
        cpi = np.prod(np.array([1+economy.inflationrate(i, units='year') for i in range(economy.date.year, date.year)]))
        consumption = (spending / cpi)
        hpi = np.prod(np.array([1+economy.depreciationrate(i, units='year') for i in range(economy.date.year, date.year)]))
        habitation = (habitation / hpi)
        return {'habitation':habitation, 'consumption':consumption}


        

















