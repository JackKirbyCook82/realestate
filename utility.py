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
__all__ = ['Household_UtilityFunction']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]
_inverse = lambda items: np.array(items).astype('float64')**-1
_normalize = lambda items: np.array(items) / np.sum(np.array(items))

utilities = CSODict()


@utilities('housing')
@UtilityFunction.register('housing', 'cobbdouglas', 'linear', parameters=('size', 'quality', 'location',), coefficents=('amplitude', 'diminishrate',))
class Housing_UtilityFunction: 
    @classmethod
    def create(cls, *args, poverty_sqft, poverty_yearbuilt, size_quality_ratio, size_location_ratio, **kwargs): 
        subsistences = {'size':int(poverty_sqft), 'quality':int(poverty_yearbuilt)}
        alpha = 1 / (1 + (1/size_quality_ratio) + (1/size_location_ratio))
        weights = {'size':alpha, 'quality':alpha/size_quality_ratio, 'location':alpha/size_location_ratio}
        coefficents = {'amplitude':1, 'diminishrate':1}
        return cls(*args, subsistences=subsistences, weights=weights, **coefficents, **kwargs)    
    
    def execute(self, *args, housing, **kwargs):
        return {'size':housing.sqft, 'location':housing.location.rank, 'quality':housing.yearbuilt}
        

@utilities('household')
@UtilityFunction.register('household', 'cobbdouglas', 'linear', parameters=('housing', 'consumption',), coefficents=('amplitude', 'diminishrate',))
class Household_UtilityFunction:
    @classmethod
    def create(cls, *args, housing_income_ratio, poverty_consumption, **kwargs): 
        functions = {'housing':Housing_UtilityFunction.create(*args, **kwargs)}
        subsistences = {'consumption':int(poverty_consumption)}
        weights = {'housing':housing_income_ratio, 'consumption':1-housing_income_ratio}
        coefficents = {'amplitude':1, 'diminishrate':1}
        return cls(*args, subsistences=subsistences, weights=weights, functions=functions, **coefficents, **kwargs)  

    def execute(self, *args, housing, consumption, **kwargs):
        return {'consumption':consumption}


        

















