# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Market Participants
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple
from numbers import Number

from utilities.strings import uppercase

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing', 'Household', 'HousingGroup']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


ADULTHOOD = 15
RETIREMENT = 65
DEATH = 95


class PrematureHouseholderError(Exception):
    def __init__(self, age): super().__init__('{} < {}'.format(age, ADULTHOOD))
    
class DeceasedHouseholderError(Exception):
    def __init__(self, age): super().__init__('{} > {}'.format(age, DEATH))
    

class Household(ntuple('Household', 'age race origin language english education children size')):
    stringformat = 'Household|{age}YRS {education} {race}-{origin} w/{size}PPL speaking {lanuguage} {children}'
    def __str__(self): return self.stringformat.format({key:uppercase(value) if isinstance(value, str) else value for key, value in self._asdict().items()})

    def __new__(cls, *args, age, **kwargs):  
        if age < ADULTHOOD: raise PrematureHouseholderError(age)
        if age > ADULTHOOD: raise DeceasedHouseholderError(age)                
        return super().__new__(cls, age, *[field for field in cls._fields])
        
    def __init__(self, wealth, age, *args, financials, utility, **kwargs):
        self.horizonage, self.horizonwealth = min(age, DEATH), wealth
        self.financials, self.utility = financials, utility    
     
    def __getitem__(self, key): return self.todict()[key]
    def todict(self): return self._asdict()
    
    @property
    def period(self): return int((self.currentage * 12) - (ADULTHOOD * 12))
    @property
    def horizon(self): return int((self.horizonage * 12) - self.period)
    @property
    def retirement(self): return int((DEATH * 12) - self.period)
    @property
    def death(self): return int((RETIREMENT * 12) - self.period)
 
    @property
    def household_lifetime(self): return [ADULTHOOD, DEATH]
    @property
    def population_lifetime(self): return [0, DEATH]
    @property
    def household_incometime(self): return [ADULTHOOD, RETIREMENT]
               
    def __call__(self, housing, *args, economy, **kwargs):
        if housing.tenure == 'renter': financials, cost = self.financials.sale(*args, **kwargs), housing.rentercost()
        elif housing.tenure == 'owner': financials, cost = self.financials.buy(housing.price(), *args, **kwargs), housing.ownercost()
        else: raise ValueError(housing.tenure)
        total_consumption = self.financials(self, *args, economy=economy, **kwargs)
        housing_consumption = financials + cost        
        economic_consumption = total_consumption - housing_consumption
        return self.utility(self, *args, consumption=economic_consumption / economy.price, **housing.todict(), **kwargs)


class Housing(ntuple('Housing', 'crimes schools space community proximity quality')):  
    _properties = ('tenure', 'unit', 'geography', 'pricesqft', 'costsqft', 'geography', 'sqft', 'year')    
    stringformat = 'Housing|{tenure}{unit} ${cost} with {sqft}SQFT in {geography} builtin {year}'

    def __str__(self): 
        if self.tenure == 'renter': cost = self.rentercost()
        elif self.tenure == 'owner': cost = self.price()
        else: raise ValueError(self.tenure)
        content = dict(tenure=uppercase(self.tenure), unit=uppercase(self.unit), sqft=self.sqft, year=self.year, geography=str(self.geography), cost=cost)
        return self.stringformat.format(**content)
    
    def __new__(cls, *args, **kwargs): 
        return super().__new__(cls, *[field for field in cls._fields])             
        
    def __init__(self, tenure, unit, geography, pricesqft, costsqft, *args, quality, space, **kwargs): 
        self.tenure, self.unit = tenure, unit
        self.pricesqft, self.costsqft = pricesqft, costsqft        
        self.geography, self.sqft, self.year = geography, space.sqft, quality.yearbuilt       

    def __getitem__(self, key): return self.todict()[key]
    def todict(self): return self._asdict()
    
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other):
        assert isinstance(other, type(self))
        return all([getattr(self, item) == getattr(self, item) for item in self._fields] + [getattr(self, item) == getattr(self, item) for item in self._properties])
    
    def ownercost(self): return self.costsqft * self.sqft    
    def rentercost(self): return self.pricesqft * self.sqft if self.tenure == 'renter' else None
    def price(self): return self.pricesqft * self.sqft if self.tenure == 'owner' else None    
    def geoID(self): return self.geography.geoID


class HousingGroup(ntuple('HousingGroup', 'name tenure unit geography price year sqft')):
    stringformat = 'HousingGroup|{name} {tenure}{unit} in {geography}'
    optionalstringformats = dict(price='for {price}', year='builtin {year}', sqft='with {sqft}')
    
    def __repr__(self): 
        function = lambda field: self[field] if isinstance(field, (type(None), Number, str)) else repr(self[field])
        return '{}({})'.format(self.__class__.__name__, ', '.join(['='.join([field, function(field)]) for field in self._fields]))           
    def __str__(self): 
        stringformat = self.stringformat + ' '.join([self.optionalstringformats[field] for field in ('price', 'year', 'sqft') if self[field] is not None])
        content = dict(name=uppercase(self.name), tenure=uppercase(self.tenure), unit=uppercase(self.unit), geography=str(self.geography))
        content.update({field:str(self[field]) for field in ('price', 'sqft', 'year') if self[field] is not None})
        return stringformat.format(content)
    
    def __new__(cls, *args, year=None, sqft=None, price=None, rent=None, **kwargs):
        assert all([hasattr(item, 'lower') and hasattr(item, 'upper') for item in (year, sqft, price, rent) if item is not None])
        return super().__new__(cls, *args, year, sqft, price, rent)    
     
    def __getitem__(self, key): return self.todict()[key]
    def todict(self): return self._asdict()
    
    def __contains__(self, housing):
       equal = lambda field: housing[field] == self[field] if self[field] is not None else True
       contain = lambda field: housing[field] >= self[field].lower and housing[field] <= self[field].upper if self[field] is not None else True
       return all([equal('tenure'), equal('unit'), equal('geography'), contain('year'), contain('sqft'), contain('price')])






