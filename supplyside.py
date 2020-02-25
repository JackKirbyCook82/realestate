# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Supply Side
@author: Jack Kirby Cook

"""

from utilities.dispatcher import clskey_singledispatcher as keydispatcher
from utilities.utility import UtilityIndex, UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_percent = lambda x, xmin, xmax: float((xmin+min(x, xmax))/(xmin+xmax))
_antipercent = lambda x: 100 - x

_MINSAT, _MAXSAT = 400, 1600
_MINACT, _MAXACT = 1, 36
_MINST, _MAXST = 1, 100


UTILITYINDEXES = dict(
    crime = {'shooting':3, 'arson':3, 'burglary':3, 'assault':2, 'vandalism':2, 'robbery':2, 'arrest':1, 'other':1, 'theft':1},
    school = {'graduation':1, 'reading':1, 'math':1, 'ap':1, 'sat':1, 'act':1, 'stratio':1, 'exp':1},
    space = {'sqft':3, 'bedrooms':2, 'rooms':1},
    proximity = {},
    quality = {},
    community = {'race':3, 'lifestage':2, 'education':1},
    consumption = {'consumption':1})


@UtilityIndex.create('inverted', UTILITYINDEXES['crime'])
class Crime_UtilityIndex: 
    def execute(self, *args, crime, **kwargs): 
        return {key:crime[key] for key in crime.keys()}

@UtilityIndex.create('tangent', UTILITYINDEXES['school'])
class School_UtilityIndex: 
    def execute(self, *args, school, **kwargs): 
        return {'gradulation':school.graduation_rate, 'reading':school.reading_rate, 'math':school.math_rate, 
                'ap':school.ap_enrollment, 'st':_percent(school.student_density, _MINST, _MAXST), 'exp':_antipercent(school.inexperience_ratio),
                'sat':_percent(school.avgsat_score, _MINSAT, _MAXSAT), 'act':_percent(school.avgact_score, _MINACT, _MAXACT)} 

@UtilityIndex.create('logarithm', UTILITYINDEXES['space'])
class Space_UtilityIndex: 
    def execute(self, *args, space, **kwargs): 
        return {key:space[key] for key in space.keys()}

@UtilityIndex.create('logarithm', UTILITYINDEXES['consumption'])
class Consumption_UtilityIndex: 
    def execute(self, *args, consumption, **kwargs): 
        return {'consumption':consumption}

@UtilityIndex.create('tangent', UTILITYINDEXES['community'])
class Community_UtilityIndex: 
    def execute(self, *args, community, race, lifestage, education, **kwargs): 
        pass ### WORKING ###

@UtilityIndex.create('inverted', UTILITYINDEXES['proximity'])
class Proximity_UtilityIndex: 
    def execute(self, *args, proximity, **kwargs): 
        pass ### WORKING ###

@UtilityIndex.create('logarithm', UTILITYINDEXES['quality'])
class Quality_UtilityIndex: 
    def execute(self, *args, quality, **kwargs): 
        pass ### WORKING ###


class Housing(dict): 
    def __init__(self, *args, **kwargs):
        super().__init__({key:kwargs[key] for key in UTILITYINDEXES.keys()})


class Household(object):  
    @keydispatcher
    def index_utility(self, key, *args, **kwargs): raise KeyError(key)
    def housing_utility(self, parameters, *args, **kwargs): return UtilityFunction.create('cobbdouglas')(parameters, amplitude=1, subsistences={}, weights={}, diminishrate=1)
    
    @index_utility.register('crime')
    def crime_utility(self, *args, **kwargs): return Crime_UtilityIndex(amplitude=1, tolerances={})
    @index_utility.register('school')
    def school_utility(self, *args, **kwargs): return School_UtilityIndex(amplitude=1, tolerances={})
    @index_utility.register('space')
    def space_utility(self, *args, **kwargs): return Space_UtilityIndex(amplitude=1, tolerances={})
    @index_utility.register('consumption')
    def consumption_utility(self, *args, **kwargs): return Consumption_UtilityIndex(amplitude=1, tolerances={})
    @index_utility.register('community')
    def community_utility(self, *args, **kwargs): return Community_UtilityIndex(amplitude=1, tolerances={})
    @index_utility.register('proximity')
    def proximity_utility(self, *args, **kwargs): return Proximity_UtilityIndex(amplitude=1, tolerances={})
    @index_utility.register('quality')
    def quality_utility(self, *args, **kwargs): return Quality_UtilityIndex(amplitude=1, tolerances={})

    def __init__(self, workers=[], domestics=[], children=[]):
        self.__workers, self.__domestics, self.__children = _aslist(workers), _aslist(domestics), _aslist(children)  
        parameters = {self.index_utility(key) for key in self.index_utility.registry().keys()}
        self.__utility = self.housing_utility(parameters, amplitude=1, subsistences={}, weights={}, diminishrate=1)

    def __call__(self, *args, housing, consumption, **kwargs):
        assert isinstance(housing, Housing)
        return self.__utility(*args, **housing, consumption=consumption, **kwargs)
         
    
class HousingMarket(object): 
    def __init__(self, households=[], housing=[]):
        assert all([isinstance(item, Household) for item in _aslist(households)])
        assert all([isinstance(item, Housing) for item in _aslist(housing)])
        self.__households, self.__housing = _aslist(households), _aslist(housing)

    def __call__(self, *args, **kwargs):
        pass ### WORKING ###




    
    
    
    
    
    
    
    
    
    
