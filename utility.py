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
@UtilityFunction.register('housing', 'cobbdouglas', parameters=('location', 'quality', 'size',), coefficents=('amplitude', 'diminishrate',))
class Housing_UtilityFunction: 
    @classmethod
    def create(cls, *args, **kwargs): 
        weights = {'location':1, 'quality':1, 'size':1}
        coefficents = {'amplitude':1, 'diminishrate':1}
        return cls(*args, weights=weights, subsistences={}, **coefficents, **kwargs)    
    
    def execute(self, *args, housing, **kwargs):
        return {'size':housing.size, 'location':housing.location, 'quality':housing.quality}
        

@utilities('household')
@UtilityFunction.register('household', 'cobbdouglas', parameters=('housing', 'consumption',), coefficents=('amplitude', 'diminishrate',))
class Household_UtilityFunction:
    @classmethod
    def create(cls, *args, **kwargs): 
        functions = {'housing':Housing_UtilityFunction.create(*args, **kwargs)}
        weights = {'housing':0.35, 'consumption':1 - 0.35}
        coefficents = {'amplitude':1, 'diminishrate':1}
        return cls(*args, subsistences={}, weights=weights, functions=functions, **coefficents, **kwargs)  

    def execute(self, *args, housing, consumption, **kwargs):
        return {'consumption':consumption}


        

















