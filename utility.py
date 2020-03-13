# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Utility Objects
@author: Jack Kirby Cook

"""

import numpy as np

from utilities.utility import UtilityIndex, UtilityFunction
from utilities.dictionarys import CallSliceOrderedDict as registry

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['UTILITY_INDEXES', 'UTILITY_FUNCTIONS']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


MINSAT, MAXSAT = 400, 1600
MINACT, MAXACT = 1, 36
MINST, MAXST = 1, 100
MINCOMMUTE, MAXCOMMUTE = 0, 120

CONSUMPTION = {'consumption':1}
CRIMES = {'shooting':3, 'arson':3, 'burglary':3, 'assault':2, 'vandalism':2, 'robbery':2, 'arrest':1, 'other':1, 'theft':1}
SCHOOLS = {'graduation':1, 'reading':1, 'math':1, 'ap':1, 'sat':1, 'act':1, 'stratio':1, 'exp':1}
QUALITY = {'age':1}
SPACE =  {'bed/ppl':3, 'sqft/ppl':2, 'sqft':1, 'sqft/bedroom':3}
PROXIMITY = {'avgcommute':1, 'midcommute':1, 'stdcommute':1}
COMMUNITY = {'race':3, 'age':2, 'children':2, 'origin':4, 'education':1, 'language':3, 'english':3}

UTILITY_INDEXES = registry()
UTILITY_FUNCTIONS = {'housing': UtilityFunction.create('cobbdouglas')}

_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]
_percent = lambda x, xmin, xmax: float((xmin+min(x, xmax))/(xmin+xmax))
_antipercent = lambda x: 100 - x


def average_records_generator(*records):
    assert all([isinstance(record, dict) for record in records])
    keys = set(_flatten([list(record.keys()) for record in records]))
    for key in keys: yield key, np.mean(_filterempty([record.get(key, None) for record in records]))


@UTILITY_INDEXES('consumption')
@UtilityIndex.create('logarithm', CONSUMPTION)
class Consumption_UtilityIndex: 
    def execute(self, household, *args, consumption, **kwargs): 
        return {'consumption':consumption}


@UTILITY_INDEXES('crime')
@UtilityIndex.create('inverted', CRIMES)
class Crime_UtilityIndex: 
    def execute(self, household, *args, crimes, **kwargs):
        crime = {key:value for key, value in average_records_generator(*crimes.values())}
        return {'shooting':crime.shooting, 'arson':crime.arson, 'burglary':crime.burglary, 'assault':crime.assault,'vandalism':crime.vandalism, 
                'robbery':crime.robbery, 'arrest':crime.arrest, 'other':crime.other, 'theft':crime.theft}


@UTILITY_INDEXES('school')
@UtilityIndex.create('tangent', SCHOOLS)
class School_UtilityIndex: 
    def execute(self, household, *args, schools, **kwargs): 
        school = {key:value for key, value in average_records_generator(*schools.values())}
        return {'gradulation':school.graduation_rate, 'reading':school.reading_rate, 'math':school.math_rate, 
                'ap':school.ap_enrollment, 'st':_percent(school.student_density, MINST, MAXST), 'exp':_antipercent(school.inexperience_ratio),
                'sat':_percent(school.avgsat_score, MINSAT, MAXSAT), 'act':_percent(school.avgact_score, MINACT, MAXACT)} 


@UTILITY_INDEXES('quality')
@UtilityIndex.create('inverted', QUALITY)
class Quality_UtilityIndex: 
    def execute(self, household, *args, quality, date, **kwargs): 
        return {'age':date.year - quality.yearbuilt + 1}


@UTILITY_INDEXES('space')
@UtilityIndex.create('logarithm', SPACE)
class Space_UtilityIndex: 
    def execute(self, household, *args, space, **kwargs): 
        return {'bed/ppl':max(space.bedrooms/household.size, 1), 'sqft/ppl':space.sqft/household.size, 'sqft':space.sqft,
                'sqft/bedroom':space.sqft * (1-(space.bedrooms/space.rooms)) / space.bedrooms}


@UTILITY_INDEXES('proximity')
@UtilityIndex.create('inverted', PROXIMITY)
class Proximity_UtilityIndex: 
    def execute(self, household, *args, proximity, **kwargs): 
        return {'avgcommute':proximity.commute.mean(bounds=[MINCOMMUTE, MAXCOMMUTE]), 'midcommute':proximity.commute.median(bounds=[MINCOMMUTE, MAXCOMMUTE]), 
                'stdcommute':proximity.commute.mean(bounds=[MINCOMMUTE, MAXCOMMUTE]) + proximity.commute.std(bounds=[MINCOMMUTE, MAXCOMMUTE])}


@UTILITY_INDEXES('community')
@UtilityIndex.create('tangent', COMMUNITY)
class Community_UtilityIndex: 
    def execute(self, household, *args, community, **kwargs): 
        category_percent = lambda attr: community[attr][household[attr]]/community[attr].total()     
        category_variable = lambda attr: community[attr].xdev(str(household[attr]))
        return {'race':category_percent('race'), 'origin':category_percent('origin'), 'language':category_percent('language'), 'children':category_percent('children'),
                'age':community.age.xdev(household.age, bounds=household.household_lifetime), 'education':category_variable('education'), 'english':category_variable('english')}























