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
from utilities.concepts import concept
from utilities.stats import MonteCarlo
from uscensus import process, renderer

from realestate.feed import Feed, Environment
from realestate.economy import Bank, School, Broker, Economy
from realestate.households import createHousehold
from realestate.housing import createHousing

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


AGE_CONSTANTS = {'adulthood':15, 'retirement':65, 'death':95}
RATE_CONSTANTS = {'wealthrate':0.05, 'discountrate':0.03, 'riskrate':2}

RATE_TABLES = {'incomerate':'Δ%avginc|geo', 'valuerate':'Δ%avgval|geo@owner', 'rentrate':'Δ%avgrent|geo@renter'}
HOUSEHOLD_TABLES = {'household':'#hh|geo', 'income':'#hh|geo|~inc', 'equity':'#hh|geo|equity', 'value':'#hh|geo|~val@owner', 'rent':'#hh|geo|~rent@renter', 'age':'#hh|geo|~age', 'size':'#hh|geo|~size', 'children':'#hh|geo|child'}
STRUCTURE_TABLES = {'structure':'#st|geo', 'unit':'#st|geo|unit', 'yearbuilt':'#st|geo|~yrblt', 'bedrooms':'#st|geo|~br', 'rooms':'#st|geo|~rm', 'sqft':'#st|geo|~sqft', 'yearoccupied':'#st|geo|~yrocc'}
POPULATION_TABLES = {'population':'#pop|geo', 'incomelevel':'#pop|geo|inclvl', 'race':'#pop|geo|race', 'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'english':'#pop|geo|eng', 'commute':'#pop|geo|~cmte'}

calculations = process()
feed = Feed(calculations, renderer, **HOUSEHOLD_TABLES, **STRUCTURE_TABLES, **POPULATION_TABLES, **RATE_TABLES)                        
concepts = {
    'count': concept('count', ['household', 'structure', 'population'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)),
    'household': concept('household', ['age', 'education', 'income', 'equity', 'value', 'yearoccupied', 'race', 'language', 'children', 'size'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)),
    'housing': concept('housing', ['unit', 'bedrooms', 'rooms', 'sqft', 'yearbuilt'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)),
    'crime': concept('crime', ['incomelevel', 'race', 'education', 'unit'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)), 
    'school': concept('school', ['language', 'education', 'race', 'english', 'income', 'value'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)),
    'proximity': concept('proximity', ['commute'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)),
    'community': concept('community',['race', 'language', 'children', 'age', 'education'], function=lambda x, *args, **kwargs: x.tohistogram(*args, how='average', **kwargs)),
    'rate': concept('rate', ['incomerate', 'valuerate', 'rentrate'], function=lambda x, *args, **kwargs: x.tocurve(*args, **kwargs))}

mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')
    
basic_school = School('basic', cost=0, duration=0, basis='year')
grade_school = School('grade', cost=0, duration=3, basis='year')
associates = School('associates', cost=25000, duration=5, basis='year')
bachelors = School('bachelors', cost=50000, duration=7, basis='year')
graduate = School('gradudate', cost=75000, duration=10, basis='year')

broker = Broker(commisions=0.03)
schools = {'uneducated':basic_school, 'gradeschool':grade_school, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
banks = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}


def createHouseholds(environment, *inputArgs, date, **inputParms):
    count = environment['count'](date=date)['household']
    for geography, in environment.iterate('geography'):
        households = environment['household'](geography=geography, date=date)
        sampler = MonteCarlo(**households.todict())
        rates=dict(wealth=RATE_CONSTANTS['wealthrate'], discount=RATE_CONSTANTS['discountrate'], risk=RATE_CONSTANTS['riskrate'], 
                   income=environment['rate'](geography=geography)['incomerate'], value=environment['rate'](geography=geography)['valuerate'])
        economy = Economy(geography, date, broker=broker, schools=schools, banks=banks, rates=rates, ages=AGE_CONSTANTS, method='average', basis='year')
        for index, values in sampler(count[geography]).iterrows(): 
#            yield createHousehold(geography, date, horizon=5, economy=economy, **values.to_dict())
            yield values

def createHousings(environment, *inputArgs, date, **inputParms):
    count = environment['count'](date=date)['structure']
    for geography, in environment.iterate('geography'):
        housings = environment['housing'](geography=geography, date=date)
        sampler = MonteCarlo(**housings.todict()) 
        rates = dict(value=environment['rate'](geography=geography)['valuerate'], rent=environment['rate'](geography=geography)['rentrate'])
        content = dict(crime=environment['crime'](geography=geography, date=date), school=environment['school'](geography=geography, date=date), 
                       proximity=environment['proximity'](geography=geography, date=date), community=environment['community'](geography=geography, date=date))
        economy = Economy(geography, date, broker=broker, schools=schools, banks=banks, rates=rates, ages=AGE_CONSTANTS, method='average', basis='year')
        for index, values in sampler(count[geography]).iterrows(): 
#            yield createHousing(geography, date, sqftprice=100, sqftrent=1, sqftcost=0.5, economy=economy, **values.to_dict(), **content)
            yield values
            

def main(*inputArgs, **inputParms):
    environment = Environment(concepts, **feed(*inputArgs, **inputParms))
    households = [household for household in createHouseholds(environment, *inputArgs, **inputParms)]
    housings = [housing for housing in createHousings(environment, *inputArgs, **inputParms)]
    
    for household in households: print(str(household))
    for housing in housings: print(str(housing))


if __name__ == '__main__':  
    tbls.set_options(linewidth=100, maxrows=40, maxcolumns=10, threshold=100, precision=2, fixednotation=True, framechar='=')
    tbls.show_options() 
    
    listparser, dictparser = ListParser(pattern=','), DictParser(pattern=',|')
    geography_parser = lambda item: Geography(dictparser(item))
    dates_parser = lambda items: [Date.fromstr(item) for item in listparser(items)]
    date_parser = lambda item: Date.fromstr(item)
    variable_parsers = {'geography':geography_parser, 'dates':dates_parser, 'date':date_parser}
    inputparser = InputParser(assignproxy='=', spaceproxy='_', parsers=variable_parsers)    
    
    print(repr(inputparser))    
    sys.argv.extend(['geography=state|6,county|29,tract|*',
                     'dates=2018,2017,2016,2015',
                     'date=2018'])
    inputparser(*sys.argv[1:])  
    main(*inputparser.inputArgs, **inputparser.inputParms)
    
 
 


















    