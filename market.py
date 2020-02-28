# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing', 'Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


Housing_Sgmts = ntuple('Housing', 'crime school space community proximity quality')
class Housing(Housing_Sgmts):  
    def __getitem__(self, key): return self.todict()[key]  
    def keys(self): return list(self.todict().keys())
    def values(self): return list(self.todict().values())
    def items(self): return zip(self.keys(), self.values())
    def todict(self): return self._asdict()


Household_Financials_Sgmts = ntuple('Households_Financials', 'income wealth value mortgage debt')
class Household_Financials(Household_Financials_Sgmts): 
    def __getitem__(self, key): return self.todict()[key]  
    def keys(self): return list(self.todict().keys())
    def values(self): return list(self.todict().values())
    def items(self): return zip(self.keys(), self.values())
    def todict(self): return self._asdict()


Household_Sgmts = ntuple('Household', 'utility age financials children size')
class Household(Household_Sgmts): 
    def __call__(self, *args, housing, consumption, **kwargs):
        assert isinstance(housing, Housing)
        return self.__utility(*args, **housing.todict(), consumption=consumption, **kwargs)
         
    
    





 
    