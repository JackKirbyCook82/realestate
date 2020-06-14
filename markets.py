# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
@name:   Real Estate Markets
@author: Jack Kirby Cook

"""

import np as numpy

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Investment_Property_Market', 'Rental_Property_Market', 'Owner_Property_Market']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class Investment_Property_Market(object):
    pass


class Rental_Property_Market(object):
    def __init__(self, *args, households=[], housings=[], **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        self.__households, self.__housings = households, housings


class Owner_Property_Market(object):
    def __init__(self, *args, households=[], housings=[], **kwargs):
        assert isinstance(households, list) and isinstance(housings, list)
        self.__households, self.__housings = households, housings

    def utility_matrix(self, tenure, horizon_years, horizon_wealth_multiple, *args, **kwargs):
        utilitymatrix = np.empty((len(self.__housing), len(self.__households)))
        for i, housing in enumerate(self.__housing):
            for j, household in enumerate(self.__households):
                try: utilitymatrix[i, j] = household.utility(housing, tenure, horizon_years, horizon_wealth_multiple, *args, **kwargs)
                except InsufficientFundsError: pass
                except InsufficientCoverageError: pass
                except UnstableLifeStyleError: pass
        return utilitymatrix














