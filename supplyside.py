# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Supply Side
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing', 'Household']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


HousingSgmts = ntuple('Housing', 'crime school space community proximity quality')
class Housing(HousingSgmts):  
    def __getitem__(self, key): return self.todict()[key]  
    def keys(self): return list(self.todict().keys())
    def values(self): return list(self.todict().values())
    def items(self): return zip(self.keys(), self.values())
    def todict(self): return self._asdict()
    

class Household(object):  
    def __init__(self, utility): self.__utility = utility
    def __call__(self, *args, housing, consumption, **kwargs):
        assert isinstance(housing, Housing)
        return self.__utility(*args, **housing.todict(), consumption=consumption, **kwargs)
         
    


    
    
    
    
    
    
    
    
    
    
