# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Valuation Application
@author: Jack Kirby Cook

"""

import sys
import numpy as np

import tables as tbls
from tables.transformations import Reduction
from variables import Geography, Date
from parsers import ListParser, DictParser
from utilities.inputparsers import InputParser

from realestate.feed import process, variables, renderer
from realestate.economy import School, Bank, Broker
from realestate.households import Household
from realestate.housing import Housing

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


WEALTH_RATE = 0.05
DISCOUNTRATE = 0.03
RISKTOLERANCE = 2
AGES = {'adulthood':15, 'retirement':65, 'death':95}

RATE_TABLES = {'income':'Δ%avginc', 'value':'Δ%avgval@owner', 'rent':'Δ%avgrent@renter'}
FINANCE_TABLES = {'income':'#hh|geo|~inc', 'value':'#hh|geo|~val', 'yearoccupied':'#st|geo|~yrocc'}
HOUSEHOLD_TABLES = {'age':'#hh|geo|~age', 'size':'#hh|geo|~size', 'children':'#hh|geo|child'}
POPULATION_TABLES = {'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'race':'#pop|geo|race'}
HOUSING_TABLES = {'yearbuilt':'#st|geo|~yrblt', 'rooms':'#st|geo|~rm', 'bedrooms':'#st|geo|~br', 'commute':'#pop|geo|~cmte'}
SIZE_TABLES = {'sqft':'#st|geo|sqft'}
CRIME_TABLES = {}
SCHOOLS_TABLES = {}        

calculations = process()
summation = Reduction(how='summation', by='summation')

arraytable = lambda tableID, *args, **kwargs: calculations[tableID](*args, **kwargs)
histtable = lambda table: summation(table, axis='geography').squeeze('geography').tohistogram()
rate = lambda table: np.average(table.arrays[table.datakeys[0]])


def main(*args, geography, date, history, **kwargs):     
    mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
    studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
    debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')
    
    basic_school = School('basisschool', cost=0, duration=0, basis='year')
    grade_school = School('gradeschool', cost=0, duration=3, basis='year')
    associates = School('associates', cost=25000, duration=5, basis='year')
    bachelors = School('bachelors', cost=50000, duration=7, basis='year')
    graduate = School('gradudate', cost=75000, duration=10, basis='year')

    broker = Broker(commisions=0.03)
    rates = {'wealth':WEALTH_RATE, 'discount':DISCOUNTRATE, 'risk':RISKTOLERANCE}
    education = {'uneducated':basic_school, 'gradeschool':grade_school, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
    banks = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}
    
    table = arraytable('#hh|geo|inc', *args, geography=geography, date=date, **kwargs)
    print(table)
    
    #rates = rates.update({key:rate(arraytable(tableID, *args, geography=geography, dates=history, **kwargs)) for key, tableID in RATE_TABLES.items()})
    #finance = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in FINANCE_TABLES.items()}
    #households = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in HOUSEHOLD_TABLES.items()}
    #housing = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in HOUSING_TABLES.items()}
    #population = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in POPULATION_TABLES.items()}
    #size = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in SIZE_TABLES.items()}
    #crime = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in CRIME_TABLES.items()}    
    #schools = {key:histtable(arraytable(tableID, *args, geography=geography, date=date, **kwargs).squeeze('date')) for key, tableID in SCHOOLS_TABLES.items()}            


if __name__ == '__main__':  
    tbls.set_options(linewidth=100, maxrows=40, maxcolumns=10, threshold=100, precision=2, fixednotation=True, framechar='=')
    tbls.show_options() 
    
    listparser, dictparser = ListParser(pattern=','), DictParser(pattern=',|')
    geography_parser = lambda item: Geography(dictparser(item))
    history_parser = lambda items: [Date.fromstr(item) for item in listparser(items)]
    date_parser = lambda item: Date.fromstr(item) if item else None
    variable_parsers = {'geography':geography_parser, 'history':history_parser, 'date':date_parser}
    inputparser = InputParser(assignproxy='=', spaceproxy='_', parsers=variable_parsers)    
    
    print(repr(inputparser))
    print(repr(process))  
    print(repr(renderer))
    print(repr(variables))
    
    sys.argv.extend(['geography=state|6,county|29,tract|*', 
                     'date=2018',
                     'history=2018,2017,2016,2015,2014'])
    inputparser(*sys.argv[1:])  
    main(*inputparser.inputArgs, **inputparser.inputParms)
    
 
 


















    