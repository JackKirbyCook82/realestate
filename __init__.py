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

from realestate.feed import Feed, environment
from realestate.economy import Bank, School, Broker, Rate

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


AGES = {'adulthood':15, 'retirement':65, 'death':95}
RATES = {'wealth':0.05, 'discount':0.03, 'risk':2}

RATE_TABLES = {'income':'Δ%avginc|geo', 'value':'Δ%avgval|geo@owner', 'rent':'Δ%avgrent|geo@renter'}
HOUSEHOLD_TABLES = {'income':'#hh|geo|~inc', 'equity':'#hh|geo|~val', 'value':'#hh|geo|~val@owner', 'rent':'#hh|geo|~rent@renter', 'age':'#hh|geo|~age', 'size':'#hh|geo|~size', 'children':'#hh|geo|child'}
STRUCTURE_TABLES = {'unit':'#st|geo|unit', 'yearbuilt':'#st|geo|~yrblt', 'bedrooms':'#st|geo|~br', 'rooms':'#st|geo|~rm', 'sqft':'#st|geo|sqft', 'yearoccupied':'#st|geo|~yrocc'}
POPULATION_TABLES = {'poverty':'#pop|geo|inclvl', 'race':'#pop|geo|race', 'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'english':'#pop|geo|eng', 'communte':'#pop|geo|~cmte'}

calculations = process()
rate_feed = Feed(calculations, renderer, **RATE_TABLES)
household_feed = Feed(calculations, renderer, **HOUSEHOLD_TABLES)
structure_feed = Feed(calculations, renderer, **STRUCTURE_TABLES)
population_feed = Feed(calculations, renderer, **POPULATION_TABLES)     

HOUSEHOLDS = ['age', 'education', 'income', 'equity', 'yearoccupied', 'race', 'language', 'children', 'size']
HOUSING = ['unit', 'bedrooms', 'rooms', 'sqft', 'yearbuilt']
CRIME = ['incomelevel', 'race', 'education', 'unit']
SCHOOL = {'language', 'education', 'race', 'english', 'income', 'value'}
PROXIMITY = {'commute'}
COMMUNITY = ['race', 'language', 'children', 'age', 'education']
RATES = ['income', 'value', 'rent']

histograms = {'crime':CRIME, 'school':SCHOOL, 'proximity':PROXIMITY, 'community':COMMUNITY}
curves = {'rates':RATES}
samples = {'households':HOUSEHOLDS, 'housing':HOUSING}
Environment = environment('Property', histograms=histograms, curves=curves, samples=samples)

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
 

def calculate(*inputArgs, geography, date, geographies, history, **inputParms):     
    rate_feed.calculate(*inputArgs, geography=geographies, dates=history, **inputParms) 
    household_feed.calculate(*inputArgs, geography=geographies, dates=date, **inputParms) 
    structure_feed.calculate(*inputArgs, geography=geographies, dates=date, **inputParms) 
    population_feed.calculate(*inputArgs, geography=geographies, dates=date, **inputParms)

#def generator(*inputArgs, geography, date, **inputParms):
#    for key, table in rate_feed(geography=geography): yield key, table
#    for feed in (household_feed, structure_feed, population_feed):
#        for key, table in feed(geography=geography, date=date): yield key, table


def main(*inputArgs, geography, date, **inputParms):
    calculate(*inputArgs, geography=geography, date=date, **inputParms)    
#    tables = {key:table for key, table in generator(*inputArgs, geography=geography, date=date, **inputParms)}
#    environment = Environment(geography=geography, date=date, **tables)    
    
    
if __name__ == '__main__':  
    tbls.set_options(linewidth=100, maxrows=40, maxcolumns=10, threshold=100, precision=2, fixednotation=True, framechar='=')
    tbls.show_options() 
    
    listparser, dictparser = ListParser(pattern=','), DictParser(pattern=',|')
    geography_parser = lambda item: Geography(dictparser(item))
    history_parser = lambda items: [Date.fromstr(item) for item in listparser(items)]
    date_parser = lambda item: Date.fromstr(item) if item else None
    variable_parsers = {'geography':geography_parser, 'geographies':geography_parser, 'history':history_parser, 'date':date_parser}
    inputparser = InputParser(assignproxy='=', spaceproxy='_', parsers=variable_parsers)    
    
    print(repr(inputparser))    
    sys.argv.extend(['geography=state|6,county|29,tract|3204',
                     'geographies=state|6,county|29,tract|*',
                     'date=2018',
                     'history=2018,2017,2016,2015,2014'])
    inputparser(*sys.argv[1:])  
    main(*inputparser.inputArgs, **inputparser.inputParms)
    
 
 


















    