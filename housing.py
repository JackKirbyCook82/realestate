# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housing Objects
@author: Jack Kirby Cook

"""

from collections import namedtuple as ntuple

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = ['Housing']
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


class Housing(ntuple('Housing', 'unit geography sqftcost rentrate valuerate crimes schools space community proximity quality')):
    stringformat = 'Housing|{unit} with {sqft}SQFT in {geography} builtin {year}|${rent:.0f}/MO Rent|${price:.0f} Purchase'       
    concepts = {} 
    
    @classmethod
    def setup(cls, *args, **kwargs): 
        attrs = {'concepts':kwargs.get('concepts', cls.concepts), 
                 'stringformat':kwargs.get('stringformat', cls.stringformat)}
        return type(cls.__name__, (cls,), attrs)    
    
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
        
    def __str__(self): 
        unit = self.__concepts['unit'][self.unit] if 'unit' in self.__concepts.keys() else self.unit
        contents = dict(sqft=self.sqft, year=self.year, geography=str(self.geography), rent=self.rentercost, price=self.price)
        return self.stringformat.format(unit=unit, **contents)          
    
    def __init__(self, *args, sqftprice, sqftrent, **kwargs): self.__sqftrent, self.__sqftprice = sqftrent, sqftprice     
    def __hash__(self): return hash((self.__class__.__name__, self.unit, hash(self.geography), self.sqftcost, hash(self.crimes), hash(self.schools), hash(self.space), hash(self.community), hash(self.proximity), hash(self.quality),))
    def __getitem__(self, key): return self.todict()[key]
    def todict(self): return self._asdict()
    
    @property
    def geoID(self): return self.geography.geoID    
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
    
#    @classmethod
#    def create(cls, *args, **kwargs):
#       crime = Crime(shooting=, arson=, burglary=, assault=, vandalism=, robbery=, arrest=, other=, theft=)
#       school = School(graduation_rate=, reading_rate=, math_rate=, ap_enrollment=, avgsat_score=, avgact_score=, student_density=, inexperience_ratio=)
#       space = Space(sqft=, bedrooms=, rooms=)
#       quality = Quality(yearbuilt=)
#       proximity = Proximity(commute=)
#       community = Community(race=, origin=, education=, language=, age=, children=)    
#       return cls()    
    
    
    
    
    
    
    
    
    
    
    
    
    