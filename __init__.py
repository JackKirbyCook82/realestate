# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Valuation Application
@author: Jack Kirby Cook

"""

import tables as tbls
from variables import Geography, Date

from realestate.feed import Rate_History, Households_MonteCarlo, Housing_MonteCarlo
from realestate.economy import School, Bank, Broker, Economy

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


tbls.set_options(linewidth=100, maxrows=40, maxcolumns=10, threshold=100, precision=3, fixednotation=True, framechar='=')
tbls.show_options()

geography = Geography(dict(state=6, county=29, tract='*'))
history = [Date(year=item) for item in range(2010, 2018 + 1)]
date = Date(year=2018)                           
      
rate_history = Rate_History(dates=history, geography=geography) 
household_montecarlo = Households_MonteCarlo(date=date, geography=geography)
housing_montecarlo = Housing_MonteCarlo(date=date, geography=geography)                  

rates = dict(wealth=(date.year, 0.03), **rate_history(geography=geography))
economy = Economy(rates=rates, projection='average', basis='year')
broker = Broker(name='ReMax', commisions=0.03)

mortgage_bank = Bank('mortgage', name='Chase', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
studentloan_bank = Bank('studentloan', name='SallyMae', rate=0.07, duration=15, basis='year')
debt_bank = Bank('debt', name='Citi', rate=0.25, duration=3, basis='year')

basic_school = School('basisschool', name='Dulles Middle School', cost=0, duration=0)
grade_school = School('gradeschool', name='Dulles High School', cost=0, duration=3)
associates = School('associates', name='DeVry', cost=25000, duration=5)
bachelors = School('bachelors', name='University of Houston', cost=50000, duration=7)
graduate = School('gradudate', name='Rice University', cost=75000, duration=10)

DISCOUNTRATE = 0.02
RISKTOLERANCE = 2
AGES = {'adulthood':15, 'retirement':65, 'death':95}
EDUCATION = {'uneducated':basic_school, 'gradeschool':grade_school, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
BANKS = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}
















    