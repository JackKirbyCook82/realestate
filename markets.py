# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Residential_PropertyMarket', 'Investment_PropertyMarket']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


class Residential_PropertyMarket(object):
    @property
    def households(self): return self.__households
    @property
    def housings(self): return self.__housings
    
    def __init__(self, *args, households, housings, **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        self.__households = households
        self.__housings = housings


class Investment_PropertyMarket(object):
    pass


