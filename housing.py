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


def createHousingKey(*args, geography, date, valuation, space, quality, variables={}, **kwargs):
    unit_index = variables['unit'](space.unit).index
    bedrooms_index = variables['bedrooms'](space.bedrooms).index
    rooms_index = variables['rooms'](space.rooms).index
    sqft_index = variables['sqft'](space.sqft).index
    yearbuilt_index = variables['yearbuilt'](quality.yearbuilt).index
    return (geography.index, date.index, int(valuation), unit_index, bedrooms_index, rooms_index, sqft_index, yearbuilt_index,)


Crime = concept('crime', ['incomelevel', 'race', 'education', 'unit'])
School = concept('school', ['language', 'education', 'english', 'income', 'value'])
Community = concept('community', ['race', 'language', 'children', 'education', 'age'])
Proximity = concept('proximity', ['commute'])
Space = concept('space', ['unit', 'bedrooms', 'rooms', 'sqft'])
Quality = concept('quality', ['yearbuilt'])


class Housing(ntuple('Housing', 'date geography valuation space quality housing neighborhood')):
    __concepts = dict(crime=Crime, school=School, community=Community, proximity=Proximity)
    __valuation = lambda *args, **kwargs: kwargs['valuation']
    __housing = tuple()
    __neighborhood = tuple()
    __variables = dict()
    
    @classmethod
    def customize(cls, *args, **kwargs):
        cls.__valuation = kwargs.get('valuation', cls.__valuation)
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
        content.update({'space':repr(self.space), 'quality':repr(self.quality)})
        content.update({'sqftrent':str(self.__sqftrent), 'sqftprice':str(self.__sqftprice), 'sqftcost':str(self.__sqftcost)})
        content.update({'neighborhood':{key:repr(self.neighborhood[key]) for key in self.__neighborhood}})
        content.update({'housing':{key:repr(self.housing[key]) for key in self.__housing}})
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

    def __init__(self, *args, sqftprice, sqftrent, sqftcost, rentrate, valuerate, variables, valuation, date, **kwargs): 
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
    def valuation(self): return self.__valuation(**self.todict())    
    @property
    def yearbuilt(self): return self.quality.yearbuilt
    @property
    def sqft(self): return self.space.sqft
    @property
    def unit(self): return self.space.unit
    
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
        valuation = cls.__valuation(**housing, **neighborhood)
        space, quality = Space(housing), Quality(housing)
        housing = {item:cls.__concepts[item](**housing) for item in cls.__housing}
        neighborhood = {item:cls.__concepts[item](**neighborhood) for item in cls.__neighborhood}
        return cls(*args, valuation=valuation, space=space, quality=quality, neightborhood=neighborhood, housing=housing, **kwargs)  
        
    
    

    
    
    
    
    
    
    
    
    
    
    
    
    