# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housing Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

from utilities.dispatchers import clskey_singledispatcher as keydispatcher
from utilities.concepts import concept

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


def createHousingKey(*args, geography, date, concepts={}, variables={}, **kwargs):
    indexes = []
    for conceptkey, conceptvalue in concepts.items():
        for field, value in conceptvalue.todict().items():
            if field in variables.keys(): indexes.append(variables[field](value).index)
            else: indexes.append(value)
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
    __variables = dict()

    @classmethod
    def customize(cls, *args, **kwargs):
        try: cls.__concepts.update(kwargs['concepts'])
        except KeyError: pass
        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)
        cls.__variables = kwargs.get('variables', cls.__variables)    
        cls.__parameters = kwargs.get('parameters', cls.__parameters)
    
    __stringformat = 'Housing[{count}]|{unit} w/ {sqft} in {geography} builtin {yearbuilt} \nPricing|${rent:.0f}/MO Rent, ${price:.0f} Purchase, ${cost:.0f}/MO Cost'           
    def __str__(self): 
        content = {field:getattr(self, field) for field in ('unit', 'sqft', 'yearbuilt',)}
        content = {key:self.__variables[key](value) if key in self.__variables.keys() else value for key, value in content.items()}
        return self.__stringformat.format(count=self.count, geography=str(self.geography), rent=self.rentercost, price=self.price, cost=self.ownercost, **content)  
    
    def __repr__(self): 
        content = {'date':repr(self.date), 'geography':repr(self.geography)} 
        content.update({'sqftrent':str(self.__sqftrent), 'sqftprice':str(self.__sqftprice), 'sqftcost':str(self.__sqftcost)})
        content.update({key:repr(value) for key, value in self.concepts.items()})
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([key, value]) for key, value in content.items()]))

    __instances = {}      
    @property
    def count(self): return self.__count
    def __new__(cls, *args, geography, date, concepts, **kwargs):   
        key = hash(createHousingKey(geography=geography, date=date, concepts=concepts, variables=cls.__variables))
        try: return cls.__instances[key]
        except KeyError:
            newinstance = super().__new__(cls, geography=geography, date=date, concepts=concepts)
            cls.__instances[key] = newinstance
            return newinstance

    def __init__(self, *args, count=1, sqftprice, sqftrent, sqftcost, rentrate, valuerate, date, **kwargs): 
        try: self.__count = self.__count + count
        except AttributeError: 
            self.__count = count 
            self.__sqftrent, self.__sqftprice, self.__sqftcost = sqftrent, sqftprice, sqftcost 
            try: self.__valuerate = valuerate(date.year, units='month')
            except TypeError: self.__discountrate
            try: self.__rentrate = rentrate(date.year, units='month')
            except TypeError: self.__discountrate              
       
    def __call__(self, supplydemandratio, *args, tenure, **kwargs):
        self.evaluate(tenure, supplydemandratio, *args, **kwargs)

    @keydispatcher
    def evaluate(self, tenure, supplydemandratio, *args, **kwargs): raise KeyError(tenure) 
    @evaluate.register('renter')
    def evaluate_renter(self, supplydemandratio, *args, **kwargs):
        self.__sqftrent = self.__sqftrent * supplydemandratio
    @evaluate.register('owner')
    def evaluate_owner(self, supplydemandratio, *args, **kwargs):
        self.__sqftprice = self.__sqftprice * supplydemandratio     
        
    def todict(self): return self._asdict()
    def __getattr__(self, attr):
        try: return self.concepts[attr]
        except KeyError: super().__getattr__(attr)
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
    def rates(self): return dict(valuerate=self.valuerate, rentrate=self.rentrate)    
    @property
    def valuerate(self): return self.__valuerate
    @property
    def rentrate(self): return self.__rentrate    
    
    @property
    def prices(self): return dict(sqftrent=self.__sqftrent, sqftprice=self.__sqftprice, sqftcost=self.__sqftcost)
    @property
    def price(self): return self.__sqftprice * self.sqft      
    @property
    def ownercost(self): return self.__sqftcost * self.sqft    
    @property
    def rentercost(self): return self.__sqftrent * self.sqft    
  
    @classmethod
    def create(cls, *args, housing={}, neighborhood={}, prices, **kwargs):         
        assert isinstance(housing, dict) and isinstance(neighborhood, dict) and isinstance(prices, dict)
        concepts = {parameter:cls.__concepts[parameter]({**housing, **neighborhood}, *args, **kwargs) for parameter in cls.__parameters}
        fields = [field for conceptkey, conceptvalue in concepts.items() for field, value in conceptvalue.todict().items()]
        assert all([field in fields for field in ('unit', 'sqft', 'yearbuilt',)])
        return cls(*args, **housing, **neighborhood, **prices, concepts=concepts, **kwargs)  
        

    
    
    
    
    
    
    
    
    
    
    
    
    