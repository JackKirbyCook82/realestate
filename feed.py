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

process = CalculationProcess('fakerealestate', name='Fake Real Estate Calculations')
renderer = CalculationRenderer(style='double', extend=1)

AGGS = {'teachers':'sum', 'students':'sum', 'count':'sum'}









