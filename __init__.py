# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Valuation Application
@author: Jack Kirby Cook

"""

from realestate.utility import UTILITY_INDEXES, UTILITY_FUNCTIONS

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


utility_indexes = {
    'crime' : UTILITY_INDEXES('crime')(amplitude=1, tolerances={}),
    'school' : UTILITY_INDEXES('school')(amplitude=1, tolerances={}),
    'space' : UTILITY_INDEXES('space')(amplitude=1, tolerances={}),
    'consumption' : UTILITY_INDEXES('consumption')(amplitude=1, tolerances={}),
    'community' : UTILITY_INDEXES('community')(amplitude=1, tolerances={}),
    'proximity' : UTILITY_INDEXES('proximity')(amplitude=1, tolerances={}),
    'quality' : UTILITY_INDEXES('quality')(amplitude=1, tolerances={})}

utility_function = UTILITY_FUNCTIONS['housing'](utility_indexes, amplitude=1, subsistences={}, weights={}, diminishrate=1)




















