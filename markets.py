# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Investment_Property_Market', 'Rental_Property_Market', 'Owner_Property_Market']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class Investment_Property_Market(object):
    pass


class Owner_Property_Market(object):
    pass


class Rental_Property_Market(object):
    def __init__(self, *args, households=[], housings=[], **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        self.__households, self.__housings = households, housings











