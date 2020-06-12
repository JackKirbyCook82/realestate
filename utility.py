# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Utility Objects
@author: Jack Kirby Cook

"""

import numpy as np

from utilities.utility import UtilityIndex, UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['UtilityIndex', 'UtilityFunction']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]


@UtilityIndex.register('spending', 'logarithm', parameters=('spending',))
class Spending_UtilityIndex: 
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)
    def execute(self, *args, housing, household, date, economy, owned, **kwargs): 
        assert isinstance(owned, bool)
        if owned: spending_expenditure = household.financials.consumption - housing.rentercost
        else: spending_expenditure = household.financials.consumption - housing.ownercost - household.financials.mortgage.payment
        factor = np.prod(np.array([economy.inflationrate(i, units='year') for i in range(economy.date.year, date.year)]))
        spending_expenditure_valuation = spending_expenditure * factor * economy.purchasingpower
        return {'spending':spending_expenditure_valuation}
    

@UtilityIndex.register('housing', 'logarithm', parameters=('housing',))
class Housing_UtilityIndex: 
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, date, **kwargs): 
        function = lambda sqft, year: (sqft / 100) + (30 - date.year - year)
        housing_expenditure_valuation = function(housing.space.sqft, housing.quality.yearbuilt)
        return {'housing':housing_expenditure_valuation}
    

@UtilityIndex.register('crime', 'rtangent', parameters=('poverty', 'nonliving', 'race', 'education', 'nonstructure', 'trailerpark',))
class Crime_UtilityIndex:
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, **kwargs):
        poverty = housing.crime.incomelevel['Poverty'] / housing.crime.incomelevel.total()
        nonliving = housing.crime.incomelevel['NonLiving'] / housing.crime.incomelevel.total()
        race = (housing.crime.race['Black'] + housing.crime.race['Other']) / housing.crime.race.total()
        education = (housing.crime.education['GradeSchool'] + housing.crime.education['Uneducated']) / housing.crime.education.total()
        nonstructure = housing.crime.unit['Vehicle'] / housing.crime.education.total()
        trailerpark = housing.crime.unit['Mobile'] / housing.crime.education.total()
        return {'poverty':poverty, 'nonliving':nonliving, 'race':race, 'education':education, 'nonstructure':nonstructure, 'trailerpark':trailerpark}


@UtilityIndex.register('school', 'tangent', parameters=('language', 'education', 'race', 'english', 'income', 'value',))
class School_UtilityIndex:
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, **kwargs):
        language = housing.school.language['English'] / housing.school.language.total()
        education = housing.school.education.xdev('Graduate')
        race = housing.school.race.xdev('Asian')
        english = housing.school.english.xdev('Fluent')
        income = housing.school.income.mean() / housing.school.income.max()
        value = housing.school.value.mean() / housing.school.income.max()
        return {'language':language, 'education':education, 'race':race, 'english':english, 'income':income, 'value':value}


@UtilityIndex.register('quality', 'inverted', parameters=('age',))
class Quality_UtilityIndex: 
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, date, **kwargs): 
        return {'age':date.year - housing.quality.yearbuilt + 1}


@UtilityIndex.register('space', 'logarithm', parameters=('bed/ppl', 'sqft/ppl', 'sqft', 'sqft/bedroom', 'unit',))
class Space_UtilityIndex: 
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, **kwargs): 
        return {'bed/ppl':max(housing.space.bedrooms/household.size, 1), 'sqft/ppl':housing.space.sqft/household.size, 'sqft':housing.space.sqft,
                'sqft/bedroom':housing.space.sqft * (1-(housing.space.bedrooms/housing.space.rooms)) / housing.space.bedrooms, 'unit':housing.space.unit}


@UtilityIndex.register('proximity', 'inverted', parameters=('avgcommute', 'midcommute', 'stdcommute',))
class Proximity_UtilityIndex: 
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, **kwargs): 
        return {'avgcommute':housing.proximity.commute.mean(), 'midcommute':housing.proximity.commute.median(), 
                'stdcommute':housing.proximity.commute.mean() + housing.proximity.commute.std()}


@UtilityIndex.register('community', 'tangent', parameters=('race', 'age', 'children', 'education', 'language',))
class Community_UtilityIndex: 
    def create(cls, *args, **kwargs): return cls(*args, amplitude=1, tolerances={}, **kwargs)    
    def execute(self, *args, housing, household, **kwargs): 
        race = housing.community.race[household.race] / housing.community.race.total()
        language = housing.community.language[household.language] / housing.community.race.total()
        children = housing.community.children[household.children] / housing.community.children.total()
        age = housing.community.age.xdev(household.age)
        education = housing.community.education.xdev(household.education)
        return {'race':race, 'age':age, 'children':children, 'education':education, 'language':language}
  

@UtilityFunction.register('cobbdouglas', 'cobbdouglas', coefficents=('elasticity',), parameters=('spending', 'housing', 'crime', 'school', 'quality', 'space', 'proximity', 'community',))
class CobbDouglas_UtilityFunction: 
    def create(cls, indexes, *args, **kwargs):        
        assert isinstance(indexes, (tuple, list))
        indexes = {UtilityIndex[parameter](*args, **kwargs) for parameter in cls.parameters if parameter in indexes}
        return cls(amplitude=1, diminishrate=1, elasticity=1, subsistences={}, weights={}, indexes=indexes)
















