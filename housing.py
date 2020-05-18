# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housing Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.concepts import concept

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['createHousing']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


def createHousing(geography, date, *args, unit, bedrooms, rooms, sqft, yearbuilt, economy, **kwargs):    
    space = Space(unit=unit, bedrooms=bedrooms, rooms=rooms, sqft=sqft)
    quality = Quality(yearbuilt=yearbuilt)
    rentrate = economy.rates['rent'](date.year) 
    valuerate = economy.rates['value'](date.year)
    return Housing(*args, date=date, geography=geography, space=space, quality=quality, rentrate=rentrate, valuerate=valuerate,  **kwargs)


Space = concept('space', ['unit', 'bedrooms', 'rooms', 'sqft'], function=int)
Quality = concept('quality', ['yearbuilt'], function=int)


class Housing(ntuple('Housing', 'date geography sqftcost rentrate valuerate crime school space community proximity quality')):
    stringformat = 'Housing|{unit} with {sqft}SQFT in {geography} builtin {year}|${rent:.0f}/MO Rent|${price:.0f} Purchase|${cost:.0f}/MO Cost'       
    def __str__(self): return self.stringformat.format(unit=self.unit, sqft=self.sqft, year=self.year, geography=str(self.geography), rent=self.rentercost, price=self.price, cost=self.ownercost)  
    
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography)} 
        content.update({'crime':repr(self.crime), 'school':repr(self.school), 'space':repr(self.space), 'community':repr(self.community), 'proximity':repr(self.proximity), 'quality':repr(self.quality)})
        content.update({field:getattr(self, field) for field in self._fields if field not in content.keys()})
        content.update({'sqftrent':self.__sqftrent, 'sqftprice':self.__sqftprice})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))
    
    def __hash__(self):
        basis = (hash(self.date), hash(self.geography),)
        concepts = (hash(self.crime), hash(self.school), hash(self.space), hash(self.community), hash(self.proximity), hash(self.quality),)
        rates = (self.rentrate, self.valuerate,)
        return hash((self.__class__.__name__, *basis, *concepts, *rates,))      
    
    __instances = {} 
    __count = 0
    @property
    def count(self): return self.__count  
    
    def __new__(cls, *args, age, **kwargs):    
        assert hasattr(kwargs['quality'], 'yearbuilt')
        assert hasattr(kwargs['space'], 'sqft')
        assert hasattr(kwargs['space'], 'unit')
        instance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
        if hash(instance) in cls.__instances: 
            cls.__instances[hash(instance)].count += 1
            return cls.__instances[hash(instance)]
        else:
            instance.__count += 1
            cls.__instances[hash(instance)] = instance
            return instance

    def __init__(self, *args, sqftprice, sqftrent, **kwargs): self.__sqftrent, self.__sqftprice = sqftrent, sqftprice     
    def __getitem__(self, key): return self.__getattr__(key)
    def todict(self): return self._asdict()
    
    @property
    def year(self): return self.quality.yearbuilt
    @property
    def sqft(self): return self.space.sqft
    @property
    def unit(self): return self.space.unit
    
    @property
    def price(self): return self.__sqftprice * self.sqft      
    @property
    def ownercost(self): return self.__sqftcost * self.sqft    
    @property
    def rentercost(self): return self.__sqftrent * self.sqft    
        
    

    
    
    
    
    
    
    