# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Valuation Application
@author: Jack Kirby Cook

"""

import numpy as np

from realestate.economy import School, Bank, Broker, Economy
from realestate.utility import Consumption_UtilityIndex, Crime_UtilityIndex, School_UtilityIndex, Quality_UtilityIndex, Space_UtilityIndex, Proximity_UtilityIndex, Community_UtilityIndex, CobbDouglas_UtilityFunction
from realestate.finance import Financials
from realestate.households import Household

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


broker = Broker(name='ReMax', commisions=0.03)

mortgagebank = Bank('mortgage', name='Chase', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
studentloanbank = Bank('studentloan', name='SallyMae', rate=0.07, duration=15, basis='year')
debtbank = Bank('debt', name='Citi', rate=0.25, duration=3, basis='year')

basicschool = School('basisschool', name='Dulles Middle School', cost=0, duration=0)
gradeschool = School('gradeschool', name='Dulles High School', cost=0, duration=3)
associates = School('associates', name='DeVry', cost=25000, duration=5)
bachelors = School('bachelors', name='University of Houston', cost=50000, duration=7)
graduate = School('gradudate', name='Rice University', cost=75000, duration=10)

DISCOUNTRATE = 0.02
RISKTOLERANCE = 2
AGES = {'adulthood':15, 'retirement':65, 'death':95}
EDUCATION = {'uneducated':basicschool, 'gradeschool':gradeschool, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
BANKS = {'mortgage':mortgagebank, 'studentloan':studentloanbank, 'debtbank':debtbank}


def create_economy(*args, **kwargs):
    
    
    economy = Economy(years, projection='average', basis='year')
    return economy


def create_utility(year, *args, **kwargs):
    crime_index = Crime_UtilityIndex(amplitude=1, tolerances={})
    school_index = School_UtilityIndex(amplitude=1, tolerances={})
    space_index = Space_UtilityIndex(amplitude=1, tolerances={})
    consumption_index = Consumption_UtilityIndex(amplitude=1, tolerances={})
    community_index = Community_UtilityIndex(amplitude=1, tolerances={})
    proximity_index = Proximity_UtilityIndex(amplitude=1, tolerances={})
    quality_index = Quality_UtilityIndex(amplitude=1, tolerances={})
    indexes = {'crime':crime_index, 'school':school_index, 'space':space_index, 'consumption':consumption_index, 'community':community_index, 'proximity':proximity_index, 'quality':quality_index}
    utility = CobbDouglas_UtilityFunction(indexes, amplitude=1, subsistences={}, weights={}, diminishrate=1)    
    return utility


def create_financials(year, *args, age, education, value, yearoccupied, income, economy, **kwargs):
    start_school = EDUCATION[education]
    start_age = AGES['adulthood'] + start_school.duration     
    start_year = year - age - start_school.duration    
    start_income = income / np.prod(np.array([1 + economy.incomerate(i, basis='year') for i in range(start_year, year)]))
    start_studentloan = BANKS['studentloan'].loan(start_school.cost)   
    assert start_age <= age and start_year <= year
    
    purchase_age = age - year - yearoccupied
    purchase_year = yearoccupied    
    purchase_value = value / np.prod(np.array([1 + economy.valuerate(i, basis='year') for i in range(purchase_year, year)]))            
    purchase_downpayment = BANKS['mortgage'].downpayment(purchase_value)
    purchase_cost = BANKS['mortgage'].cost(purchase_value - purchase_downpayment)
    purchase_cash = purchase_downpayment - purchase_cost    
    assert start_year <= purchase_year <= year and start_age <= purchase_age <= age
    
    targets = {purchase_age - start_age:purchase_cash}
    financials = Financials(max(AGES['death'] - start_age, 0), max(AGES['retirement'] - start_age, 0), targets=targets, terminalwealth=0, discountrate=DISCOUNTRATE, risktolerance=RISKTOLERANCE, 
                            income=start_income, wealth=0, value=0, mortgage=None, studentloan=start_studentloan, debt=None, **economy.rates(year, basis='year'), basis='year')
    financials = financials.projection(max(purchase_age - start_age, 0), **economy.rates(year, basis='year'), basis='year')
    financials = financials.buy(purchase_value, bank=BANKS['mortgage'])
    financials = financials.projection(max(age - purchase_age, 0), **economy.rates(year, basis='year'), basis='year')    
    return financials


def create_household(year, *args, age, education, race, origin, language, children, size, **kwargs):
    financials = create_financials(*args, age=age, education=education, **kwargs)
    utility = create_utility(*args, **kwargs)
    household = Household(age=age, race=race, origin=origin, language=language, education=education, children=children, size=size, financials=financials, utility=utility)
    return household
    




















    