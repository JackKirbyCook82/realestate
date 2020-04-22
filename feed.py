# -*- coding: utf-8 -*-
"""
Created on Tues Apr 7 2020
@name:   Real Estate Feed Objects
@author: Jack Kirby Cook

"""

import os.path
import numpy as np
import scipy.stats as stats

import tables as tbls
from uscensus import renderer
from uscensus import process as uscensus_process
from uscensus import variables as uscensus_variables
from specs import specs_fromfile
from variables import Variables
from parsers import DictorListParser

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['process', 'renderer', 'variables']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


DIR = os.path.dirname(os.path.realpath(__file__))
SPECS_FILE = os.path.join(DIR, 'specs.csv')

AGGS = {'teachers':'sum', 'students':'sum', 'count':'sum'}

specsparsers = {'databasis': DictorListParser(pattern=';=')}
specs = specs_fromfile(SPECS_FILE, specsparsers)
custom_variables = Variables.create(**specs, name='RealEstate')
noncustom_variables = Variables.load('date', 'geography', name='RealEstate')
variables = uscensus_variables.copy(name='RealEstate')
variables = variables.update(custom_variables)
variables = variables.update(noncustom_variables)
process = uscensus_process.copy('realestate', name='RealEstate')


#percent_tables = {'%grad|geo|schlvl@student': {'tables':['#pop|geo|race', '#hh|geo|~inc'], 'parms':{}},
#                  '%ap|geo|schlvl@student': {'tables':['#pop|geo|race', '#hh|geo|~inc'], 'parms':{}}, 
#                  '%sat|geo|schlvl@student': {'tables':['#pop|geo|race', '#hh|geo|~inc'], 'parms':{}},
#                  '%act|geo|schlvl@student': {'tables':['#pop|geo|race', '#hh|geo|~inc'], 'parms':{}},
#                  '%read|geo|schlvl@student': {'tables':['#pop|geo|race', '#hh|geo|~inc'], 'parms':{}},
#                  '%math|geo|schlvl@student': {'tables':['#pop|geo|race', '#hh|geo|~inc'], 'parms':{}},                  
#                  '%exp|geo|schlvl@teacher': {'tables':['#hh|geo|~inc'], 'parms':{}}}
#@process.create(**percent_tables)    
#def percent_pipeline(tabelID, *args, geography, date, **kwargs):
#    pass
#
#
#student_tables = {'#pop|geo|schlvl@student': {'tables': '#pop|geo|schlvl', 'parms':{}}}
#@process.create(**student_tables)
#def student_pipeline(tableID, *args, **kwargs):
#    pass
#
#
#teacher_pipeline = {'#pop|geo|schlvl@teacher': {'tables': '#pop|geo|schlvl', 'parms':{}}}
#@process.create(**teacher_pipeline)
#def teacher_pipeline(tableID, *args, **kwargs):
#    pass
#
#
#ratio_tables = {'%pop|geo|schlvl': {'tables': ['#pop|geo|schlvl@teacher', '#pop|geo|schlvl@student'], 'parms':{}}}        
#@process.create(**ratio_tables)
#def ratio_pipeline(tableID, *args, **kwargs):
#    pass    


   








