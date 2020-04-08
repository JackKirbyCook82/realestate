# -*- coding: utf-8 -*-
"""
Created on Tues Apr 7 2020
@name:   Real Estate Fake Feed Objects
@author: Jack Kirby Cook

"""

import os.path
import numpy as np

import tables as tbls
from tables.processors import CalculationProcess, CalculationRenderer
from tables.transformations import Scale, GroupBy
from specs import specs_fromfile
from variables import Variables, Date, Geography
from parsers import DictorListParser

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['process', 'renderer', 'variables']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


DIR = os.path.dirname(os.path.realpath(__file__))
SPECS_FILE = os.path.join(DIR, 'specs.csv')

specsparsers = {'databasis': DictorListParser(pattern=';=')}
specs = specs_fromfile(SPECS_FILE, specsparsers)
custom_variables = Variables.create(**specs, name='Fake Real Estate')
noncustom_variables = Variables.load('date', 'geography', name='Fake Real Estate')
variables = custom_variables.update(noncustom_variables)

minmax = Scale(how='minmax')
groupby = GroupBy(how='groups', agg='sum')

process = CalculationProcess('fakerealestate', name='Fake Real Estate Calculations')
renderer = CalculationRenderer(style='double', extend=1)

AGGS = {'teachers':'sum', 'students':'sum', 'count':'sum'}


feed_tables = {
    '#ct|geo|crime': {},
    '#teach|geo|schlvl':{},
    '#stu|geo|schlvl':{},
    'avgSAT|geo|schlvl':{},
    'avgACT|geo|schlvl':{},
    '%grad|geo|schlvl':{},
    '%ap|geo|schlvl':{},
    '%math|geo|schlvl':{},
    '%read|geo|schlvl':{},
    '#teach|geo|exp|schlvl':{}}

ratio_tables = {
    'stu/teach|geo|schlvl': {
        'tables': ['#stud|geo|schlvl', '#teach|geo|schlvl'],
        'parms': {'formatting':{'precision':0}}}}

minmax_tables = {
    '%avgSAT|geo|schlvl': {
        'tables':'avgSAT|geo|schlvl',
        'parms':{'axis':None, 'minimum':400, 'maximum':1600}},
    '%avgACT|geo|schlvl': {
        'tables':'avgACT|geo|schlvl',
        'parms':{'axis':None, 'minimum':1, 'maximum':36}}}
       
split_tables = {
    '#teach|geo|~exp|schlvl': {
        'tables': '#teach|geo|exp|schlvl',
        'parms': {'axis':'exp', 'groups':[2]}}}
        

@process.create(**feed_tables)
def feed_pipeline(tableID, *args, **kwargs):
    pass

@process.create(**ratio_tables)
def ratio_pipeline(tableID, toptable, bottomtable, *args, **kwargs):
    table = tbls.operations.divide(toptable, bottomtable, *args, **kwargs).fillinf(np.NaN)
    return table

@process.create(**minmax_tables)
def minmax_pipeline(tableID, table, *args, axis,  minimum, maximum, **kwargs):
    table = minmax(table, *args, axis=axis, minimum=minimum, maximum=maximum, **kwargs)
    return table

@process.create(**split_tables)
def split_pipeline(tableID, table, *args, axis, **kwargs):
    pass















