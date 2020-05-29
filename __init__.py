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
from uscensus import process, renderer

from realestate.feed import Feed, Data, Environment, MonteCarlo
from realestate.economy import Bank, Education, Broker
from realestate.households import createHousehold
from realestate.housing import createHousing

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


RATES = {'wealthrate':0.05, 'discountrate':0.03}
AGES = {'adulthood':15, 'retirement':65, 'death':95} 

RATE_TABLES = {'incomerate':'Δ%avginc|geo', 'valuerate':'Δ%avgval|geo@owner', 'rentrate':'Δ%avgrent|geo@renter'}
HOUSEHOLD_TABLES = {'households':'#hh|geo', 'income':'#hh|geo|~inc', 'value':'#hh|geo|equity', 'rent':'#hh|geo|lease', 'age':'#hh|geo|~age', 'size':'#hh|geo|~size', 'children':'#hh|geo|child'}
STRUCTURE_TABLES = {'structures':'#st|geo', 'unit':'#st|geo|unit', 'yearbuilt':'#st|geo|~yrblt', 'bedrooms':'#st|geo|~br', 'rooms':'#st|geo|~rm', 'sqft':'#st|geo|~sqft', 'yearoccupied':'#st|geo|~yrocc'}
POPULATION_TABLES = {'population':'#pop|geo', 'incomelevel':'#pop|geo|inclvl', 'race':'#pop|geo|race', 'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'english':'#pop|geo|eng', 'commute':'#pop|geo|~cmte'}

calculations = process()
feed = Feed(calculations, renderer, **HOUSEHOLD_TABLES, **STRUCTURE_TABLES, **POPULATION_TABLES, **RATE_TABLES)                        
concepts = {
    'household': concept('household', ['age', 'education', 'income', 'value', 'yearoccupied', 'race', 'language', 'children', 'size']),
    'housing': concept('housing', ['unit', 'bedrooms', 'rooms', 'sqft', 'yearbuilt']),
    'crime': concept('crime', ['incomelevel', 'race', 'education', 'unit']), 
    'school': concept('school', ['language', 'education', 'race', 'english', 'income', 'value']),
    'proximity': concept('proximity', ['commute']),
    'community': concept('community',['race', 'language', 'children', 'age', 'education'])}

mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')
    
basic = Education('basic', cost=0, duration=0, basis='year')
grade = Education('grade', cost=0, duration=3, basis='year')
associates = Education('associates', cost=25000, duration=5, basis='year')
bachelors = Education('bachelors', cost=50000, duration=7, basis='year')
graduate = Education('gradudate', cost=75000, duration=10, basis='year')

broker = Broker(commisions=0.03)
educations = {'uneducated':basic, 'gradeschool':grade, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
banks = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}


def createHousings(environment):
    if environment['structures'] <= 0: print('Empty Geography: {}, {} Structures\n'.format(str(environment.geography), environment['structures']))
    else: 
        housingsampler = MonteCarlo(**environment['housing'].todict())  
        rates = dict(valuerate=environment['valuerate'], rentrate=environment['rentrate'])
        content = dict(crime=environment['crime'], school=environment['school'], proximity=environment['proximity'], community=environment['community'])
        for index, values in housingsampler(environment['structures']):               
            yield createHousing(environment.geography, environment.date, sqftprice=100, sqftrent=1, sqftcost=0.5, ages=AGES, **rates, **values, **content)        

def createHouseholds(environment):        
    if environment['households'] <= 0: print('Empty Geography: {}, {} Households\n'.format(str(environment.geography), environment['households']))
    else: 
        householdsampler = MonteCarlo(**environment['household'].todict())
        rates = dict(wealthrate=environment['wealthrate'], discountrate=environment['discountrate'], incomerate=environment['incomerate'], valuerate=environment['valuerate'])
        for index, values in householdsampler(environment['households']): 
            yield createHousehold(environment.geography, environment.date, horizon=5, ages=AGES, **rates, **values)
        

def main(*inputArgs, date, **inputParms):
    data = Data(**feed(*inputArgs, **inputParms))
    for geography, in data.iterate('geography'):
        tables = data(geography=geography)
        environment = Environment(geography, date, tables=tables, concepts=concepts, extrapolate='average', basis='year', **RATES)
        households = [household for household in createHouseholds(environment)]
        housings = [housing for housing in createHousings(environment)]
        

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
    
 
 


















    