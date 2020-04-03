# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Valuation Application
@author: Jack Kirby Cook

"""

from scipy.linalg import cholesky, eigh

import tables as tbls
from variables import Geography, Date

from realestate.economy import School, Bank, Broker

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


















    