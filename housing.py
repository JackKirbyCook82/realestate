# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housing Objects
@author: Jack Kirby Cook

"""

import pandas as pd
from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from utilities.strings import uppercase
from utilities.concepts import concept

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


def createHousingKey(*args, geography, date, concepts={}, **kwargs):
    indexes = [value for conceptkey, conceptvalue in concepts.items() for field, value in conceptvalue.todict().items()]
    return (geography.index, date.index, *indexes)        


Crime = concept('crime', ['incomelevel', 'race', 'education', 'unit'])
School = concept('school', ['language', 'education', 'english', 'income', 'value'])
Community = concept('community', ['race', 'language', 'children', 'education', 'age'])
Proximity = concept('proximity', ['commute'])
Space = concept('space', ['unit', 'bedrooms', 'rooms', 'sqft'])
Quality = concept('quality', ['yearbuilt'])


class Housing(ntuple('Housing', 'geography date concepts')):
    __concepts = dict(space=Space, quality=Quality, crime=Crime, school=School, community=Community, proximity=Proximity)
    __parameters = ('space', 'quality', 'crime', 'school', 'community', 'proximity',)

    @classmethod
    def clear(cls): cls.__instances = {}
    @classmethod
    def customize(cls, *args, **kwargs):
        cls.clear()
        cls.__parameters = kwargs.get('parameters', cls.__parameters)
        try: cls.__concepts.update(kwargs['concepts'])
        except KeyError: pass 

    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography)} 
        content.update({'rent':str(self.__rent), 'price':str(self.__price), 'sqftcost':str(self.__sqftcost)})
        content.update({key:repr(value) for key, value in self.concepts.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    __instances = {}      
    @property
    def count(self): return self.__count
    def __new__(cls, *args, geography, date, concepts, **kwargs):   
        key = hash(createHousingKey(geography=geography, date=date, concepts=concepts))
        try: return cls.__instances[key]
        except KeyError:
            newinstance = super().__new__(cls, geography=geography, date=date, concepts=concepts)
            cls.__instances[key] = newinstance
            return newinstance

    def __init__(self, *args, count=1, price, rent, sqftcost, rentrate, valuerate, date, **kwargs): 
        try: self.__count = self.__count + count
        except (AttributeError, KeyError): 
            self.__count = count 
            self.__rent, self.__price, self.__sqftcost = rent, price, sqftcost 
            self.__valuerate = valuerate(date.year, units='month')
            self.__rentrate = rentrate(date.year, units='month')           
         
    def __call__(self, price, *args, tenure, **kwargs):
        self.updateprice(tenure, price, *args, **kwargs)

    @keydispatcher
    def updateprice(self, tenure, price, *args, **kwargs): raise KeyError(tenure) 
    @updateprice.register('renter')
    def updateprice_renter(self, price, *args, **kwargs): self.__rent = price
    @updateprice.register('owner')
    def updatepricee_owner(self, price, *args, **kwargs): self.__price = price  
    
    def todict(self): return self._asdict()
    def __getattr__(self, attr): return self.concepts[attr]
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))
 
    @property
    def key(self): return hash(createHousingKey(**self.todict()))   
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return all([self.key == other.key, self.rates == other.rates, self.prices == other.prices])  

    @property
    def unit(self): return self.getfield('unit')
    @property
    def sqft(self): return self.getfield('sqft')
    @property
    def yearbuilt(self): return self.getfield('yearbuilt')   
    def getfield(self, field):
        for conceptkey, conceptvalue in self.concepts.items():
            try: return getattr(conceptvalue, field)
            except AttributeError: pass
        raise KeyError(field)    
     
    @property
    def valuerate(self): return self.__valuerate
    @property
    def rentrate(self): return self.__rentrate    
    
    @property
    def purchaseprice(self): return self.__price    
    @property
    def ownercost(self): return self.__sqftcost * self.sqft    
    @property
    def rentercost(self): return self.__rent 

    @keydispatcher
    def price(self, tenure): raise KeyError(tenure)
    @price.register('renter', 'rent')
    def priceRenter(self): return self.__rent
    @price.register('owner', 'own')
    def priceOwner(self): return self.__price

    def toSeries(self):
        content = {'count':self.count, 'geography':self.geography.geoID, 'unit':self.unit, 'sqft':self.sqft, 'yearbuilt':self.yearbuilt}
        content.update({'price':self.__price, 'rent':self.__rent})
        series = pd.Series(content)
        return series
      
    @classmethod 
    def table(cls, tenure=None):
        dataframe = pd.concat([housing.toSeries() for housing in cls.__instances.values()], axis=1).transpose()
        if tenure == 'renter': dataframe.drop('price', axis=1, inplace=True)
        elif tenure == 'owner': dataframe.drop('rent', axis=1, inplace=True)
        else: pass
        dataframe.columns = [uppercase(column) for column in dataframe.columns]
        dataframe.index.name = 'Housings'
        return dataframe        
    
    @classmethod
    def create(cls, *args, housing={}, neighborhood={}, prices, **kwargs):         
        assert isinstance(housing, dict) and isinstance(neighborhood, dict) and isinstance(prices, dict)
        concepts = {parameter:cls.__concepts[parameter]({**housing, **neighborhood}, *args, **kwargs) for parameter in cls.__parameters}
        fields = [field for conceptkey, conceptvalue in concepts.items() for field, value in conceptvalue.todict().items()]
        assert all([field in fields for field in ('unit', 'sqft', 'yearbuilt',)])
        return cls(*args, **housing, **neighborhood, **prices, concepts=concepts, **kwargs)  
        

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    