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

from realestate.feed import Feed, createConcept, createEnvironment
from realestate.households import createHousehold
from realestate.housing import createHousing
from realestate.economy import Bank, School, Broker, Rate

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


AGE_CONSTANTS = {'adulthood':15, 'retirement':65, 'death':95}
RATE_CONSTANTS = {'wealthrate':0.05, 'discountrate':0.03, 'riskrate':2}

RATE_TABLES = {'incomerate':'Δ%avginc|geo', 'valuerate':'Δ%avgval|geo@owner', 'rentrate':'Δ%avgrent|geo@renter'}
HOUSEHOLD_TABLES = {'households':'#hh|geo', 'income':'#hh|geo|~inc', 'equity':'#hh|geo|~equity', 'value':'#hh|geo|~val@owner', 'rent':'#hh|geo|~rent@renter', 'age':'#hh|geo|~age', 'size':'#hh|geo|~size', 'children':'#hh|geo|child'}
STRUCTURE_TABLES = {'structures':'#st|geo', 'unit':'#st|geo|unit', 'yearbuilt':'#st|geo|~yrblt', 'bedrooms':'#st|geo|~br', 'rooms':'#st|geo|~rm', 'sqft':'#st|geo|sqft', 'yearoccupied':'#st|geo|~yrocc'}
POPULATION_TABLES = {'population':'#pop|geo', 'incomelevel':'#pop|geo|inclvl', 'race':'#pop|geo|race', 'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'english':'#pop|geo|eng', 'communte':'#pop|geo|~cmte'}

calculations = process()
feed = Feed(calculations, renderer, **HOUSEHOLD_TABLES, **STRUCTURE_TABLES, **POPULATION_TABLES, **RATE_TABLES)                        
  
concepts = {
    'count': createConcept('counts', histograms=['households', 'structures', 'population']),
    'household': createConcept('households', histograms=['age', 'education', 'income', 'equity', 'value', 'yearoccupied', 'race', 'language', 'children', 'size']),
    'housing': createConcept('housing', histograms=['unit', 'bedrooms', 'rooms', 'sqft', 'yearbuilt']),
    'crime': createConcept('crime', histograms=['incomelevel', 'race', 'education', 'unit']),
    'crimeRace': createConcept('crimeRace', histograms=['race']),
    'crimeWealth': createConcept('crimeWealth', histograms=['incomelevel']),
    'school': createConcept('school', histograms=['language', 'education', 'race', 'english', 'income', 'value']),
    'schoolEducation': createConcept('schoolEducation', histograms=['education']),
    'schoolEnglish': createConcept('schoolEnglish', histograms=['language', 'english']),
    'schoolWealth': createConcept('schoolWealth', ['income', 'value']),
    'proximity': createConcept('proximity', histograms=['commute']),
    'community': createConcept('community', histograms=['race', 'language', 'children', 'age', 'education']),
    'rates': createConcept('rates', curves=['incomerate', 'valuerate', 'rentrate'])}

Environment = createEnvironment('market', concepts=concepts)

mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')
    
basic_school = School('basic', cost=0, duration=0, basis='year')
grade_school = School('grade', cost=0, duration=3, basis='year')
associates = School('associates', cost=25000, duration=5, basis='year')
bachelors = School('bachelors', cost=50000, duration=7, basis='year')
graduate = School('gradudate', cost=75000, duration=10, basis='year')

broker = Broker(commisions=0.03)
education = {'uneducated':basic_school, 'gradeschool':grade_school, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
banks = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}


def createHouseholds(environment, *inputArgs, date, **inputParms):
    pass

#    counts = environment['counts'](date=date)['households']
#    for geography in environment.iterate('geography'):
#        households = MonteCarlo(**environment['households'](geography=geography, basis='year', date=date).todict())
#        incomerate = Rate.fromcurve(environment['income'](geography=geography, basis='year', method='average'))(date)
#        valuerate = Rate.fromcurve(environment['value'](geography=geography), basis='year', method='average')(date)
#        wealthrate = Rate.frompoint(RATE_CONSTANTS['wealth'], basis='year')(date)
#        discountrate = Rate.frompoint(RATE_CONSTANTS['discount'], basis='year')(date)
#        riskrate = Rate.frompoint(RATE_CONSTANTS['risk'], basis='year')(date)
#        meta = dict(geography=geography, date=date)
#        content = dict(incomerate=incomerate, valuerate=valuerate, wealthrate=wealthrate, discountrate=discountrate, riskrate=riskrate)
#        for index, values in households(counts[geography]).iterrows(): 
#            yield createHousehold(horizon=5, **values.to_dict(), **content, **meta, broker=broker, education=education, banks=banks)


def createHousings(environment, *inputArgs, date, **inputParms):
    pass

#    counts = environment['counts'](date=date)['structures']
#    for geography in environment.iterate('geography'):
#        housings = MonteCarlo(**environment['housings'](geography=geography, date=date).todict())
#        crime = environment['crime'](geography=geography, date=date)
#        school = environment['school'](geography=geography, date=date)
#        proximity = environment['proximity'](geography=geography, date=date)
#        community = environment['community'](geography=geography, date=date)    
#        valuerate = Rate.fromcurve(environment['value'](geography=geography), basis='year', method='average')(date)
#        rentrate = Rate.fromcurve(environment['rent'](geography=geography), basis='year', method='average')(date)
#        meta = dict(geography=geography, date=date)
#        content = dict(crime=crime, school=school, proximity=proximity, community=community, valuerate=valuerate, rentrate=rentrate)
#        for index, values in housings(counts[geography]).iterrows(): 
#            yield createHousing(sqftprice=100, sqftrent=1, sqftcost=0.5, **values.to_dict(), **content, **meta, broker=broker, education=education, banks=banks)
        

def main(*inputArgs, **inputParms):
    with feed(Environment, *inputArgs, **inputParms) as environment:
        households = [household for household in createHouseholds(environment, *inputArgs, **inputParms)]
        housings = [housing for housing in createHousings(environment, *inputArgs, **inputParms)]
    
    for household in households: print(str(household))
    for housing in housings: print(str(housing))


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
    
 
 


















    