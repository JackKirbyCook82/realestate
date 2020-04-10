# -*- coding: utf-8 -*-
"""
Created on Tues Apr 7 2020
@name:   Real Estate Feed Objects
@author: Jack Kirby Cook

"""

import os.path

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

specsparsers = {'databasis': DictorListParser(pattern=';=')}
specs = specs_fromfile(SPECS_FILE, specsparsers)
custom_variables = Variables.create(**specs, name='RealEstate')
noncustom_variables = Variables.load('date', 'geography', name='RealEstate')
variables = uscensus_variables.copy(name='RealEstate')
variables = variables.update(custom_variables)
variables = variables.update(noncustom_variables)
process = uscensus_process.copy('realestate', name='RealEstate')

AGGS = {'teachers':'sum', 'students':'sum', 'count':'sum'}









