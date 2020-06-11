# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Utility Objects
@author: Jack Kirby Cook

"""

import numpy as np

from utilities.utility import UtilityIndex, CobbDouglas_UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing_UtilityIndex', 'Consumption_UtilityIndex', 'Crime_UtilityIndex', 'School_UtilityIndex', 'Quality_UtilityIndex', 
           'Space_UtilityIndex', 'Proximity_UtilityIndex', 'Community_UtilityIndex', 'CobbDouglas_UtilityFunction']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]


@UtilityIndex.create('consumption', 'logarithm', {'consumption':1})
class Consumption_UtilityIndex: 
    def __init__(self, *args, dateCPI, indexCPI=1, **kwargs):
        self.__date, self.__indexCPI = dateCPI, indexCPI
        super().__init__(*args, **kwargs)
        
    def execute(self, *args, housing, household, date, inflationrate, **kwargs): 
        factor = np.prod(np.array([inflationrate(i, units='year') for i in range(self.__date.year, date.year)]))
        return {'consumption':household.financials.consumption * factor * self.__indexCPI}


@UtilityIndex.create('housing', 'logarithm', {'housing':1})
class Housing_UtilityIndex: 
    def execute(self, *args, housing, household, **kwargs): 
        return {'housing':housing.valuation}
    

@UtilityIndex.create('crime', 'rtangent', {'poverty':3, 'nonliving':2, 'race':1, 'education':2, 'nonstructure':3, 'trailerpark':1})
class Crime_UtilityIndex:
    def execute(self, *args, housing, household, **kwargs):
        poverty = housing.crime.incomelevel['Poverty'] / housing.crime.incomelevel.total()
        nonliving = housing.crime.incomelevel['NonLiving'] / housing.crime.incomelevel.total()
        race = (housing.crime.race['Black'] + housing.crime.race['Other']) / housing.crime.race.total()
        education = (housing.crime.education['GradeSchool'] + housing.crime.education['Uneducated']) / housing.crime.education.total()
        nonstructure = housing.crime.unit['Vehicle'] / housing.crime.education.total()
        trailerpark = housing.crime.unit['Mobile'] / housing.crime.education.total()
        return {'poverty':poverty, 'nonliving':nonliving, 'race':race, 'education':education, 'nonstructure':nonstructure, 'trailerpark':trailerpark}


@UtilityIndex.create('school', 'tangent', {'language':1, 'education':1, 'race':1, 'english':3, 'income':2, 'value':2})
class School_UtilityIndex:
    def execute(self, *args, housing, household, **kwargs):
        language = housing.school.language['English'] / housing.school.language.total()
        education = housing.school.education.xdev('Graduate')
        race = housing.school.race.xdev('Asian')
        english = housing.school.english.xdev('Fluent')
        income = housing.school.income.mean() / housing.school.income.max()
        value = housing.school.value.mean() / housing.school.income.max()
        return {'language':language, 'education':education, 'race':race, 'english':english, 'income':income, 'value':value}


@UtilityIndex.create('quality', 'inverted', {'age':1})
class Quality_UtilityIndex: 
    def execute(self, *args, housing, household, date, **kwargs): 
        return {'age':date.year - housing.quality.yearbuilt + 1}


@UtilityIndex.create('space', 'logarithm', {'bed/ppl':3, 'sqft/ppl':2, 'sqft':1, 'sqft/bedroom':3, 'unit':1})
class Space_UtilityIndex: 
    def execute(self, *args, housing, household, **kwargs): 
        return {'bed/ppl':max(housing.space.bedrooms/household.size, 1), 'sqft/ppl':housing.space.sqft/household.size, 'sqft':housing.space.sqft,
                'sqft/bedroom':housing.space.sqft * (1-(housing.space.bedrooms/housing.space.rooms)) / housing.space.bedrooms, 'unit':housing.space.unit}


@UtilityIndex.create('proximity', 'inverted', {'avgcommute':1, 'midcommute':1, 'stdcommute':1})
class Proximity_UtilityIndex: 
    def execute(self, *args, housing, household, **kwargs): 
        return {'avgcommute':housing.proximity.commute.mean(), 'midcommute':housing.proximity.commute.median(), 
                'stdcommute':housing.proximity.commute.mean() + housing.proximity.commute.std()}


@UtilityIndex.create('community', 'tangent', {'race':4, 'age':2, 'children':2, 'education':1, 'language':3})
class Community_UtilityIndex: 
    def execute(self, *args, housing, household, **kwargs): 
        race = housing.community.race[household.race] / housing.community.race.total()
        language = housing.community.language[household.language] / housing.community.race.total()
        children = housing.community.children[household.children] / housing.community.children.total()
        age = housing.community.age.xdev(household.age)
        education = housing.community.education.xdev(household.education)
        return {'race':race, 'age':age, 'children':children, 'education':education, 'language':language}
  


















