# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Valuation Application
@author: Jack Kirby Cook

"""

import sys
import numpy as np
from scipy.interpolate import interp1d
from scipy.linalg import cholesky, eigh

import tables as tbls
from tables.transformations import Reduction
from variables import Geography, Date
from parsers import ListParser, DictParser
from utilities.inputparsers import InputParser
from uscensus import process, renderer

from realestate.economy import School, Bank, Broker, Rate, Environment
from realestate.households import Household
from realestate.housing import Housing


__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


WEALTH_RATE = 0.03
DISCOUNTRATE = 0.02
RISKTOLERANCE = 2
AGES = {'adulthood':15, 'retirement':65, 'death':95}

RATE_TABLES = {'income':'Δ%avginc', 'value':'Δ%avgval@owner', 'rent':'Δ%avgrent@renter'}
HOUSING_TABLES = {'yearoccupied':'#st|geo|yrblt', 'rooms':'#st|geo|rm', 'bedrooms':'#st|geo|br', 'commute':'#pop|geo|cmte'}
FINANCE_TABLES = {'income':'#hh|geo|~inc', 'value':'#hh|geo|~val', 'rent':'#hh|geo|~rent'}
HOUSEHOLD_TABLES = {'age':'#hh|geo|~age', 'yearoccupied':'#st|geo|~yrocc', 'size':'#hh|geo|~size', 'children':'#hh|geo|child', 
                    'education':'#pop|geo|edu', 'language':'#pop|geo|lang', 'race':'#pop|geo|race', 'origin':'#pop|geo|origin'}

calculations = process()
summation = Reduction(how='summation', by='summation')
arraytable = lambda tableID, *args, **kwargs: calculations[tableID](*args, **kwargs)
histtable = lambda tableID, *args, **kwargs: summation(arraytable(tableID, *args, **kwargs), *args, axis='geography', **kwargs).squeeze('geography').tohistogram()
x = lambda table: np.array([table.variables['date'].fromstr(string).value for string in table.headers['date']])
y = lambda table: table.arrays[table.datakeys[0]]
rate = lambda key, table: Rate(key, x(table), y(table), method='average', basis='year')


def main(*args, geography, date, history, **kwargs):     
    print(str(inputparser), '\n')  
    print(str(calculations), '\n')
    
    rate_arraytables = {key:arraytable(tableID, *args, geography=geography, dates=history, **kwargs) for key, tableID in RATE_TABLES.items()}
    #finance_histograms = {key:histtable(tableID, *args, geography=geography, date=date, **kwargs) for key, tableID in FINANCE_TABLES.items()}
    #household_histograms = {key:histtable(tableID, *args, geography=geography, date=date, **kwargs) for key, tableID in HOUSEHOLD_TABLES.items()}
    #housing_histograms = {key:histtable(tableID, *args, geography=geography, date=date, **kwargs) for key, tableID in HOUSING_TABLES.items()}

    #rates = {'wealth':Rate('wealth', int(date.year), WEALTH_RATE), **{key:rate(key, table) for key, table in rate_arraytables.items()}}
    #environment = Environment(date=date, geography=geography, rates=rates, finance=finance_histograms, households=household_histograms, housing=housing_histograms)

    for key, table in rate_arraytables.items():
        print(key)
        print(table)


if __name__ == '__main__':  
    tbls.set_options(linewidth=100, maxrows=40, maxcolumns=10, threshold=100, precision=3, fixednotation=True, framechar='=')
    tbls.show_options()
    
    listparser, dictparser = ListParser(pattern=','), DictParser(pattern=',|')
    geography_parser = lambda item: Geography(dictparser(item))
    history_parser = lambda items: [Date.fromstr(item) for item in listparser(items)]
    date_parser = lambda item: Date.fromstr(item) if item else None
    variable_parsers = {'geography':geography_parser, 'history':history_parser, 'date':date_parser}
    inputparser = InputParser(assignproxy='=', spaceproxy='_', parsers=variable_parsers)    
    
    print(repr(inputparser))
    print(repr(renderer))
    print(repr(process), '\n')  
    
    sys.argv.extend(['geography=state|6,county|29,tract|*', 
                     'date=2018',
                     'history=2018,2017,2016'])
    inputparser(*sys.argv[1:])
    main(*inputparser.inputArgs, **inputparser.inputParms)
    
 
    
    
#broker = Broker(commisions=0.03)

#mortgage_bank = Bank('mortgage', rate=0.05, duration=30, financing=0.03, coverage=0.03, loantovalue=0.8, basis='year')
#studentloan_bank = Bank('studentloan', rate=0.07, duration=15, basis='year')
#debt_bank = Bank('debt', rate=0.25, duration=3, basis='year')

#basic_school = School('basisschool', cost=0, duration=0, basis='year')
#grade_school = School('gradeschool', cost=0, duration=3, basis='year')
#associates = School('associates', cost=25000, duration=5, basis='year')
#bachelors = School('bachelors', cost=50000, duration=7, basis='year')
#graduate = School('gradudate', cost=75000, duration=10, basis='year')

#EDUCATION = {'uneducated':basic_school, 'gradeschool':grade_school, 'associates':associates, 'bachelors':bachelors, 'graduate':graduate}
#BANKS = {'mortgage':mortgage_bank, 'studentloan':studentloan_bank, 'debtbank':debt_bank}

#class MonteCarlo(object):
#    __instances = {}
#    def __new__(cls, *args, geography, date, **kwargs):
#        key = hash((cls.__name__, hash(date), hash(geography),))
#        instance = cls.__instances.get(key, super().__new__(cls))
#        if key not in cls.__instances.keys(): cls.__instances[key] = instance
#        return instance
#
#    def __init__(self, tables, *args, **kwargs):
#        self.__tables = {key:gettable(tableID, *args, **kwargs) for key, tableID in self.tableIDs.items()}
#        self.__correlationmatrix = np.zero((len(self), len(self)))
#        np.fill_diagonal(self.__correlationmatrix, 1)
#        
#    def __call__(self, size, *args, **kwargs):
#        if 'geography' in kwargs.keys(): tables = {key:table[{'geography':kwargs['geography']}] for key, table in self.__tables.items()}
#        else: tables = {key:self.summation(table, *args, axis='geography', weights=self.__weights, **kwargs) for key, table in self.__tables.items()}
#        tables = {key:table.tohistorgram() for key, table in tables.items()}
#        concepts = ODict([(table.axiskey, table.concepts) for table in tables.values()])
#        keys = [table.axiskey for table in tables.values()]
#        samplematrix = self.__samplematrix(tables, size, *args, **kwargs)                      
#        
#    def __samplematirx(self, tables, size, *args, method='cholesky', **kwargs):
#        samplematrix = np.array([table(size) for table in tables.values()]) 
#        if method == 'cholesky':
#            correlation_matrix = cholesky(self.__correlationmatrix, lower=True)
#        elif method == 'eigen':
#            evals, evecs = eigh(self.__correlationmatrix)
#            correlation_matrix = np.dot(evecs, np.diag(np.sqrt(evals)))
#        else: raise ValueError(method)
#        return np.dot(correlation_matrix, samplematrix).transpose()     


















    