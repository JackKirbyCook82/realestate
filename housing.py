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
    space = Space(dict(unit=unit, bedrooms=bedrooms, rooms=rooms, sqft=sqft))
    quality = Quality(dict(yearbuilt=yearbuilt))
    rentrate = economy.rates['rent'](date.year) 
    valuerate = economy.rates['value'](date.year)
    return Housing(*args, date=date, geography=geography, space=space, quality=quality, rentrate=rentrate, valuerate=valuerate, **kwargs)

#def createHousingKey(*args, date, geography, space, quality, **kwargs):
#    return ('Housing', hash(date), hash(geography), hash(space), hash(quality),) 

Space = concept('space', ['unit', 'bedrooms', 'rooms', 'sqft'])
Quality = concept('quality', ['yearbuilt'])


class Housing(ntuple('Housing', 'date geography rentrate valuerate crime school space community proximity quality')):
#    __instances = {}     
    __stringformat = 'Housing[count]|{unit} with {sqft} in {geography} builtin {year}, ${rent:.0f}/MO Rent, ${price:.0f} Purchase, ${cost:.0f}/MO Cost'           
    def __str__(self): return self.__stringformat.format(count=self.count, unit=self.unit, sqft=self.sqft, year=self.year, geography=str(self.geography), rent=self.rentercost, price=self.price, cost=self.ownercost)  
    
#    def __hash__(self): raise Exception('HASH TABLE REQUIRED')
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography)} 
        content.update({'crime':repr(self.crime), 'school':repr(self.school), 'space':repr(self.space), 'community':repr(self.community), 'proximity':repr(self.proximity), 'quality':repr(self.quality)})
        content.update({field:repr(getattr(self, field)) for field in self._fields if field not in content.keys()})
        content.update({'sqftrent':str(self.__sqftrent), 'sqftprice':str(self.__sqftprice)})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

#    @classmethod
#    def counts(cls): return [instance.count for instance in cls.__instances.values()]

#    @property
#    def count(self): return self.__count
#    def addcount(self): self.__count += 1
    
#    def __new__(cls, *args, **kwargs):   
#        key = createHousingKey(*args, **kwargs)
#        if hash(key) in cls.__instances.keys(): 
#            cls.__instances[key].addcount()
#            return cls.__instances[key]
#        else:
#            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
#            cls.__instances[key] = newinstance
#            return newinstance

    def __init__(self, *args, sqftprice, sqftrent, sqftcost, **kwargs): 
        self.__sqftrent, self.__sqftprice, self.__sqftcost = sqftrent, sqftprice, sqftcost     
        self.__count = 1

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))
    
    @property
    def year(self): return self.quality.yearbuilt
    @property
    def sqft(self): return self.space.sqft
    @property
    def unit(self): return self.space.unit
    
    @property
    def price(self): return self.__sqftprice * self.sqft.value      
    @property
    def ownercost(self): return self.__sqftcost * self.sqft.value    
    @property
    def rentercost(self): return self.__sqftrent * self.sqft.value    
        
    

    
    
    
    
    
    
    