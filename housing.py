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
__all__ = ['Housing']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class RequiredFieldMissingError(Exception): pass


def createHousingKey(*args, geography, date, housing={}, variables={}, **kwargs):
    housing_indexes  = []
    for conceptkey, conceptvalue in sorted(housing.items()):
        for field, value in sorted(conceptvalue.todict().items()):
            housing_indexes.append(variables[field](value).index if field in variables.keys() else value)
    return (geography.index, date.index, *housing_indexes)


def transverse(field, **concepts):
    for conceptkey, conceptvalue in concepts.todict().items():
        try: return conceptvalue[field]
        except KeyError: pass
    raise RequiredFieldMissingError()


Crime = concept('crime', ['incomelevel', 'race', 'education', 'unit'])
School = concept('school', ['language', 'education', 'english', 'income', 'value'])
Community = concept('community', ['race', 'language', 'children', 'education', 'age'])
Proximity = concept('proximity', ['commute'])
Space = concept('space', ['unit', 'bedrooms', 'rooms', 'sqft'])
Quality = concept('quality', ['yearbuilt'])


class Housing(ntuple('Housing', 'date geography housing neighborhood')):
    __concepts = dict(space=Space, quality=Quality, crime=Crime, school=School, community=Community, proximity=Proximity)
    __housing = tuple()
    __neighborhood = tuple()
    __variables = dict()
    
    @classmethod
    def customize(cls, *args, **kwargs):
        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)
        cls.__variables = kwargs.get('variables', cls.__variables)    
        cls.__concepts = kwargs.get('concepts', cls.__concepts)
        cls.__neighborhood = kwargs.get('neighborhood', cls.__housing)     
        cls.__housing = kwargs.get('housing', cls.__neighborhood)     
    
    __stringformat = 'Housing[{count}]|{unit} w/ {sqft} in {geography} builtin {yearbuilt} \nPricing|${rent:.0f}/MO Rent, ${price:.0f} Purchase, ${cost:.0f}/MO Cost'           
    def __str__(self): 
        content = {field:getattr(self, field) for field in ('unit', 'sqft', 'yearbuilt',)}
        content = {field:self.__variables[field](value) if field in self.__valuation.keys() else value for field, value in content.items()}
        return self.__stringformat.format(count=self.count, geography=str(self.geography), rent=self.rentercost, price=self.price, cost=self.ownercost, **content)  
    
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography)} 
        content.update({'sqftrent':str(self.__sqftrent), 'sqftprice':str(self.__sqftprice), 'sqftcost':str(self.__sqftcost)})
        content.update({'neighborhood':{conceptkey:repr(self.neighborhood[conceptkey]) for conceptkey in self.__neighborhood}})
        content.update({'housing':{conceptkey:repr(self.housing[conceptkey]) for conceptkey in self.__housing}})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    __instances = {}      
    @property
    def count(self): return self.__count
    def __new__(cls, *args, **kwargs):   
        key = hash(createHousingKey(*args, **kwargs))
        try: return cls.__instances[key]
        except KeyError:
            newinstance = super().__new__(cls, **{field:kwargs[field] for field in cls._fields})
            cls.__instances[key] = newinstance
            return newinstance

    def __init__(self, *args, sqftprice, sqftrent, sqftcost, rentrate, valuerate, date, **kwargs): 
        self.__sqftrent, self.__sqftprice, self.__sqftcost = sqftrent, sqftprice, sqftcost 
        try: self.__valuerate = valuerate(date.year, units='month')
        except TypeError: self.__discountrate
        try: self.__rentrate = rentrate(date.year, units='month')
        except TypeError: self.__discountrate               
        try: self.__count = self.__count + 1
        except AttributeError: self.__count = 1

    def todict(self): return self._asdict()
    def __getitem__(self, item): 
        if isinstance(item, (int, slice)): return super().__getitem__(item)
        elif isinstance(item, str): return getattr(self, item)
        else: raise TypeError(type(item))

    @property
    def key(self): return hash(createHousingKey(**self.todict(), variables=self.__variables))    
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        assert isinstance(other, type(self))
        return all([self.key == other.key, self.rates == other.rates, self.prices == other.prices])  

    @property
    def sqft(self): return transverse('sqft', self.housing)
    @property
    def unit(self): return transverse('unit', self.housing)
    @property
    def yearbuilt(self): return transverse('yearbuilt', self.housing)
    
    @property
    def valuerate(self): return self.__valuerate
    @property
    def rentrate(self): return self.__rentrate    
    
    @property
    def price(self): return self.__sqftprice * self.sqft      
    @property
    def ownercost(self): return self.__sqftcost * self.sqft    
    @property
    def rentercost(self): return self.__sqftrent * self.sqft    
  
    @classmethod
    def create(cls, *args, housing={}, neighborhood={}, **kwargs):         
        assert isinstance(housing, dict) and isinstance(neighborhood, dict)
        housing = {conceptkey:cls.__concepts[conceptkey](**housing) for conceptkey in cls.__housing}
        neighborhood = {conceptkey:cls.__concepts[conceptkey](**neighborhood) for conceptkey in cls.__neighborhood}        
        transverse('sqft', housing) 
        transverse('unit', housing) 
        transverse('yearbuilt', housing)
        return cls(*args, housing=housing, neightborhood=neighborhood, **kwargs)  
        
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    