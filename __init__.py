# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Valuation Application
@author: Jack Kirby Cook

"""

from variables import Crime, School, Space, Community, Proximity, Quality, Date
from variables.fields import RaceHistogram, OriginHistogram, EducationHistogram, LanguageHistogram, EnglishHistogram, ChildrenHistogram, AgeHistogram, CommuteHistogram

from realestate.utility import UTILITY_INDEXES, UTILITY_FUNCTIONS
from realestate.market import Rates, Durations, Economy, Loan, Financials, Housing, Household

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


indexes = {
    'crime' : UTILITY_INDEXES['crime'](amplitude=1, tolerances={}),
    'school' : UTILITY_INDEXES['school'](amplitude=1, tolerances={}),
    'space' : UTILITY_INDEXES['space'](amplitude=1, tolerances={}),
    'consumption' : UTILITY_INDEXES['consumption'](amplitude=1, tolerances={}),
    'community' : UTILITY_INDEXES['community'](amplitude=1, tolerances={}),
    'proximity' : UTILITY_INDEXES['proximity'](amplitude=1, tolerances={}),
    'quality' : UTILITY_INDEXES['quality'](amplitude=1, tolerances={})}

utility = UTILITY_FUNCTIONS['housing'](indexes, amplitude=1, subsistences={}, weights={}, diminishrate=1)

rates = Rates('yearly', discount=0.02, wealth=0.03, value=0.03, income=0.03, mortgage=0.04, studentloan=0.06, debt=0.2)
durations = Durations('yearly', child=18, life=95, income=65, mortgage=30, studentloan=20, debt=3)
economy = Economy(rates=rates, durations=durations, risk=1, price=1, commisions=0.3, financing=0.3, coverage=3, loantovalue=0.8)

mortgage = Loan(name='mortgage', balance=140000 + 275000, rate=rates.mortgage, duration=durations.mortgage*0.8)
studentloan = Loan(name='studentloan', balance=35000, rate=rates.studentloan, duration=durations.studentloan*0.8)
debt = Loan(name='debt', balance=5000, rate=rates.debt, duration=durations.debt)

financials = Financials(wealth=230000, income=130000, value=200000 + 265000, mortgage=mortgage, studentloan=studentloan, debt=debt)
household = Household(250000, 42, financials=financials, utility=utility, age=37, race='White', education='Graduate', origin='NonHispanic', language='English', english='Fluent', children='W/Children', size=4)

race = {'White', 'Black', 'Native', 'Asian', 'Islander', 'Other', 'Mix'}
origin = {'NonHispanic', 'Hispanic'}
education = {'Uneducated', 'GradeSchool', 'Associates', 'Bachelors', 'Graduate'}
language = {'English', 'Spanish', 'IndoEuro', 'Asian', 'Pacific', 'African', 'Native', 'Arabic', 'Other'}
english = {'Fluent', 'Well', 'Poor', 'Inable'}
children = {'W/OChildren', 'WChildren'}
age = {'15 YRS|24 YRS', '25 YRS|34 YRS', '35 YRS|44 YRS', '45 YRS|54 YRS', '55 YRS|59 YRS', '60 YRS|64 YRS', '65 YRS|74 YRS', '75 YRS|84 YRS', '>85 YRS'}
commute = {'<4 MINS', '5 MINS|9 MINS', '10 MINS|14 MINS', '15 MINS|19 MINS', '20 MINS|24 MINS', '25 MINS|29 MINS', '30 MINS|34 MINS', '35 MINS|39 MINS', '40 MINS|44 MINS', '45 MINS|59 MINS', '60 MINS|89 MINS', '>90 MINS'}

racehistogram = RaceHistogram(race)
originhistogram = OriginHistogram(origin)
educationhistogram = EducationHistogram(education)
languagehistogram = LanguageHistogram(language)
englishhistogram = EnglishHistogram(english)
childrenhistogram = ChildrenHistogram(children)
agehistogram = AgeHistogram(age)
commutehistogram = CommuteHistogram(commute)

attributes = {
    'crime' : {
        'spotcrime':Crime(shooting=0, arson=0, burglary=0, assault=0, vandalism=0, robbery=0, arrest=4, other=3, theft=8),
        'mylocalcrime':Crime(shooting=0, arson=0, burglary=0, assault=0, vandalism=0, robbery=0, arrest=8, other=6, theft=12)},
    'school' : {
        'elementry':School(reading_rate=0.8, math_rate=0.7, student_density=30, inexperience_ratio=0.2),
        'middle':School(reading_rate=0.75, math_rate=0.75, student_density=30, inexperience_ratio=0.15),
        'high':School(graduation_rate=0.95, reading_rate=0.85, math_rate=0.65, ap_enrollment=0.25, avgsat_score=1225, avgact_score=25, student_density=30, inexperience_ratio=0.1)},
    'space' : Space(sqft=1500, bedrooms=3, rooms=6),
    'quality' : Quality(yearbuilt=2000), 
    'proximity' : Proximity(commute=commutehistogram),  
    'community' : Community(race=racehistogram, origin=originhistogram, education=educationhistogram, language=languagehistogram, english=englishhistogram, children=childrenhistogram, age=agehistogram)}

housing = Housing(cost=1750, rent=3000, price=400000, unit='House', **attributes)
utility = household('owner', housing, economy=economy, date=Date(year=2020))













