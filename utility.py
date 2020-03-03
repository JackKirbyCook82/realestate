# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Utility
@author: Jack Kirby Cook

"""

from utilities.utility import UtilityIndex, UtilityFunction
from utilities.dictionarys import CallSliceOrderedDict as registry

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['UTILITY_INDEXES', 'UTILITY_FUNCTIONS']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


UTILITY_INDEXES = registry()
UTILITY_FUNCTIONS = {'housing': UtilityFunction.create('cobbdouglas')}

MINSAT, MAXSAT = 400, 1600
MINACT, MAXACT = 1, 36
MINST, MAXST = 1, 100

_percent = lambda x, xmin, xmax: float((xmin+min(x, xmax))/(xmin+xmax))
_antipercent = lambda x: 100 - x


@UTILITY_INDEXES('crime')
@UtilityIndex.create('inverted', {'shooting':3, 'arson':3, 'burglary':3, 'assault':2, 'vandalism':2, 'robbery':2, 'arrest':1, 'other':1, 'theft':1})
class Crime_UtilityIndex: 
    def execute(self, *args, crime, **kwargs): 
       return {'shooting':crime.shooting, 'arson':crime.arson, 'burglary':crime.burglary, 'assault':crime.assault,'vandalism':crime.vandalism, 
               'robbery':crime.robbery, 'arrest':crime.arrest, 'other':crime.other, 'theft':crime.theft}


@UTILITY_INDEXES('school')
@UtilityIndex.create('tangent', {'graduation':1, 'reading':1, 'math':1, 'ap':1, 'sat':1, 'act':1, 'stratio':1, 'exp':1})
class School_UtilityIndex: 
    def execute(self, *args, school, **kwargs): 
        return {'gradulation':school.graduation_rate, 'reading':school.reading_rate, 'math':school.math_rate, 
                'ap':school.ap_enrollment, 'st':_percent(school.student_density, MINST, MAXST), 'exp':_antipercent(school.inexperience_ratio),
                'sat':_percent(school.avgsat_score, MINSAT, MAXSAT), 'act':_percent(school.avgact_score, MINACT, MAXACT)} 


@UTILITY_INDEXES('space')
@UtilityIndex.create('logarithm', {'sqft':3, 'bedrooms':2, 'rooms':1})
class Space_UtilityIndex: 
    def execute(self, *args, space, **kwargs): 
        return {'sqft':space.sqft, 'bedrooms':space.bedrooms, 'rooms':space.rooms}


@UTILITY_INDEXES('consumption')
@UtilityIndex.create('logarithm', {'consumption':1})
class Consumption_UtilityIndex: 
    def execute(self, *args, consumption, **kwargs): 
        return {'consumption':consumption}


@UTILITY_INDEXES('community')
@UtilityIndex.create('tangent', {})
class Community_UtilityIndex: 
    def execute(self, *args, community, **kwargs): 
        pass 


@UTILITY_INDEXES('proximity')
@UtilityIndex.create('inverted', {})
class Proximity_UtilityIndex: 
    def execute(self, *args, proximity, **kwargs): 
        pass 


@UTILITY_INDEXES('quality')
@UtilityIndex.create('logarithm', {})
class Quality_UtilityIndex: 
    def execute(self, *args, quality, **kwargs): 
        pass



