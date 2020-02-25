# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Demand Side
@author: Jack Kirby Cook

"""
__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


_aslist = lambda items: [items] if not isinstance(items, (list, tuple)) else list(items)


class Child(object): 
    def __init__(self, age, race): 
        self.__age, self.__race = age, race
    
class Domestic(object): 
    def __init__(self, age, race):
        self.__age, self.__race = age, race

class Worker(object): 
    def __init__(self, age, race, industry, occupation, education):      
        self.__age, self.__race = age, race
        self.__industry, self.__occupation = industry, occupation
        self.__education = education


class Job(object): 
    def __init__(self, industry, occupation, education, income):
        self.__industry, self.__occupation = industry, occupation
        self.__education = education
        self.__income = income


class LaborMarket(object): 
    def __init__(self, workers=[], jobs=[]):
        assert all([isinstance(worker, Worker) for worker in _aslist(workers)])
        assert all([isinstance(job, Job) for job in _aslist(jobs)])
        self.__workers, self.__jobs = _aslist(workers), _aslist(jobs)