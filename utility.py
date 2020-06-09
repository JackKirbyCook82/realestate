# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Utility Objects
@author: Jack Kirby Cook

"""

from utilities.utility import UtilityIndex, UtilityFunction

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['createUtility']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_flatten = lambda nesteditems: [item for items in nesteditems for item in items]
_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)
_filterempty = lambda items: [item for item in _aslist(items) if item]


def createUtility(geography, date, *args, **kwargs):
    consumption = UtilityIndex.create('consumption', *args, amplitude=1, tolerances={}, **kwargs)
    crime = UtilityIndex.create('crime', *args, amplitude=1, tolerances={}, **kwargs)
    school = UtilityIndex.create('school', *args, amplitude=1, tolerances={}, **kwargs)
    quality = UtilityIndex.create('quality', *args, amplitude=1, tolerances={}, **kwargs)
    space = UtilityIndex.create('space', *args, amplitude=1, tolerances={}, **kwargs)
    proximity = UtilityIndex.create('proximity', *args, amplitude=1, tolerances={}, **kwargs)
    community = UtilityIndex.create('community', *args, amplitude=1, tolerances={}, **kwargs)
    indexes = dict(consumption=consumption, crime=crime, school=school, quality=quality, space=space, proximity=proximity, community=community)
    return UtilityFunction.create('cobbdouglas', *args, amplitude=1, subsistences={}, weights={}, diminishrate=1, indexes=indexes, **kwargs)

#def createUtility(geography, date, *args, **kwargs):
#    pass


@UtilityIndex.register('consumption', 'logarithm', {'consumption':1})
class Consumption_UtilityIndex: 
    def execute(self, housing, household, *args, **kwargs): 
        return {'consumption':household.netconsumption}


@UtilityIndex.register('crime', 'rtangent', {'poverty':3, 'nonliving':2, 'race':1, 'education':2, 'nonstructure':3, 'trailerpark':1})
class Crime_UtilityIndex:
    def execute(self, housing, household, *args, **kwargs):
        poverty = housing.crime.incomelevel['Poverty'] / housing.crime.incomelevel.total()
        nonliving = housing.crime.incomelevel['NonLiving'] / housing.crime.incomelevel.total()
        race = (housing.crime.race['Black'] + housing.crime.race['Other']) / housing.crime.race.total()
        education = (housing.crime.education['GradeSchool'] + housing.crime.education['Uneducated']) / housing.crime.education.total()
        nonstructure = housing.crime.unit['Vehicle'] / housing.crime.education.total()
        trailerpark = housing.crime.unit['Mobile'] / housing.crime.education.total()
        return {'poverty':poverty, 'nonliving':nonliving, 'race':race, 'education':education, 'nonstructure':nonstructure, 'trailerpark':trailerpark}


@UtilityIndex.register('school', 'tangent', {'language':1, 'education':1, 'race':1, 'english':3, 'income':2, 'value':2})
class School_UtilityIndex:
    def execute(self, housing, household, *args, **kwargs):
        language = housing.school.language['English'] / housing.school.language.total()
        education = housing.school.education.xdev('Graduate')
        race = housing.school.race.xdev('Asian')
        english = housing.school.english.xdev('Fluent')
        income = housing.school.income.mean() / housing.school.income.max()
        value = housing.school.value.mean() / housing.school.income.max()
        return {'language':language, 'education':education, 'race':race, 'english':english, 'income':income, 'value':value}


@UtilityIndex.register('quality', 'inverted', {'age':1})
class Quality_UtilityIndex: 
    def execute(self, housing, household, *args, date, **kwargs): 
        return {'age':date.year - housing.quality.yearbuilt + 1}


@UtilityIndex.register('space', 'logarithm', {'bed/ppl':3, 'sqft/ppl':2, 'sqft':1, 'sqft/bedroom':3, 'unit':1})
class Space_UtilityIndex: 
    def execute(self, housing, household, *args, **kwargs): 
        return {'bed/ppl':max(housing.space.bedrooms/household.size, 1), 'sqft/ppl':housing.space.sqft/household.size, 'sqft':housing.space.sqft,
                'sqft/bedroom':housing.space.sqft * (1-(housing.space.bedrooms/housing.space.rooms)) / housing.space.bedrooms, 'unit':housing.space.unit}


@UtilityIndex.register('proximity', 'inverted', {'avgcommute':1, 'midcommute':1, 'stdcommute':1})
class Proximity_UtilityIndex: 
    def execute(self, housing, household, *args, **kwargs): 
        return {'avgcommute':housing.proximity.commute.mean(), 'midcommute':housing.proximity.commute.median(), 
                'stdcommute':housing.proximity.commute.mean() + housing.proximity.commute.std()}


@UtilityIndex.register('community', 'tangent', {'race':4, 'age':2, 'children':2, 'education':1, 'language':3})
class Community_UtilityIndex: 
    def execute(self, housing, household, *args, **kwargs): 
        race = housing.community.race[household.race] / housing.community.race.total()
        language = housing.community.language[household.language] / housing.community.race.total()
        children = housing.community.children[household.children] / housing.community.children.total()
        age = housing.community.age.xdev(household.age)
        education = housing.community.education.xdev(household.education)
        return {'race':race, 'age':age, 'children':children, 'education':education, 'language':language}
  


















