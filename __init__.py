# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Valuation Application
@author: Jack Kirby Cook

"""

import sys

import tables as tbls
from variables import Geography, Date
from parsers import ListParser, DictParser
from utilities.inputparsers import InputParser
from uscensus import process, renderer

from realestate.feed import Feed, MonteCarlo, create_environment
from realestate.economy import Bank, School, Broker, Rate

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


AGE_CONSTANTS = {'adulthood':15, 'retirement':65, 'death':95}
RATE_CONSTANTS = {'wealth':0.05, 'discount':0.03, 'risk':2}

RATE_TABLES = {'income':'Δ%avginc|geo', 'value':'Δ%avgval|geo@owner', 'rent':'Δ%avgrent|geo@renter'}
HOUSEHOLD_TABLES = {'income':'#hh|geo|~inc', 'equity':'#hh|geo|~equity', 'value':'#hh|geo|~val@owner', 'rent':'#hh|geo|~rent@renter', 'age':'#hh|geo|~age', 'size':'#hh|geo|~size', 'children':'#hh|geo|child'}
STRUCTURE_TABLES = {'unit':'#st|geo|unit', 'yearbuilt':'#st|geo|~yrblt', 'bedrooms':'#st|geo|~br', 'rooms':'#st|geo|~rm', 'sqft':'#st|geo|sqft', 'yearoccupied':'#st|geo|~yrocc'}
POPULATION_TABLES = {'incomelevel':'#pop|geo|inclvl', 'race':'#pop|geo|race', 'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'english':'#pop|geo|eng', 'communte':'#pop|geo|~cmte'}

HOUSEHOLDS = ['age', 'education', 'income', 'equity', 'value', 'yearoccupied', 'race', 'language', 'children', 'size']
HOUSING = ['unit', 'bedrooms', 'rooms', 'sqft', 'yearbuilt']
CRIME = ['incomelevel', 'race', 'education', 'unit']
SCHOOL = ['language', 'education', 'race', 'english', 'income', 'value']
PROXIMITY = ['commute']
COMMUNITY = ['race', 'language', 'children', 'age', 'education']
RATES = ['income', 'value', 'rent']

tohistogram = lambda table, *args, **kwargs: table.tohistogram(*args, **kwargs)
tocurve = lambda table, *args, **kwargs: table.tocurve(*args, **kwargs)

calculations = process()
feed = Feed(calculations, renderer, **HOUSEHOLD_TABLES, **STRUCTURE_TABLES, **POPULATION_TABLES, **RATE_TABLES)   
concepts = {'households':HOUSEHOLDS, 'housing':HOUSING, 'crime':CRIME, 'school':SCHOOL, 'proximity':PROXIMITY, 'community':COMMUNITY, 'rates':RATES}
Environment = create_environment('market', concepts=concepts, functions={item:tocurve for item in RATES}, default=tohistogram)

mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')
    
basic_school = School('basisschool', cost=0, duration=0, basis='year')
grade_school = School('gradeschool', cost=0, duration=3, basis='year')
associates = School('associates', cost=25000, duration=5, basis='year')
bachelors = School('bachelors', cost=50000, duration=7, basis='year')
graduate = School('gradudate', cost=75000, duration=10, basis='year')

broker = Broker(commisions=0.03)
education = {'uneducated':basic_school, 'gradeschool':grade_school, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
banks = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}


def main(*inputArgs, date, **inputParms):
    with feed(Environment, *inputArgs, **inputParms) as environment:
        for geography in environment.iterate('geography'):
            households = MonteCarlo(**environment['households'](geography=geography, date=date).todict())
            housing = MonteCarlo(**environment['housing'](geography=geography, date=date).todict())
            crime = environment['crime'](geography=geography, date=date)
            school = environment['school'](geography=geography, date=date)
            proximity = environment['proximity'](geography=geography, date=date)
            community = environment['community'](geography=geography, date=date)        
            income = Rate.fromcurve(environment['income'](geography=geography))(date)
            value = Rate.fromcurve(environment['value'](geography=geography))(date)
            rent = Rate.fromcurve(environment['rent'](geography=geography))(date)
            wealth = Rate.frompoint(date.index, RATE_CONSTANTS['wealth']) (date)
            discount = Rate.frompoint(date.index, RATE_CONSTANTS['discount'])(date) 
            risk = Rate.frompoint(date.index, RATE_CONSTANTS['risk']) (date)
            break
    

if __name__ == '__main__':  
    tbls.set_options(linewidth=100, maxrows=40, maxcolumns=10, threshold=100, precision=2, fixednotation=True, framechar='=')
    tbls.show_options() 
    
    listparser, dictparser = ListParser(pattern=','), DictParser(pattern=',|')
    geography_parser = lambda item: Geography(dictparser(item))
    history_parser = lambda items: [Date.fromstr(item) for item in listparser(items)]
    date_parser = lambda item: Date.fromstr(item) if item else None
    variable_parsers = {'geography':geography_parser, 'date':date_parser, 'history':history_parser}
    inputparser = InputParser(assignproxy='=', spaceproxy='_', parsers=variable_parsers)    
    
    print(repr(inputparser))    
    sys.argv.extend(['geography=state|6,county|29,tract|*',
                     'history=2018,2017,2016',
                     'date=2018'])
    inputparser(*sys.argv[1:])  
    main(*inputparser.inputArgs, **inputparser.inputParms)
    
 
 


















    