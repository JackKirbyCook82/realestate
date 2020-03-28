# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 2020
@name:   Real Estate Housing Objects
@author: Jack Kirby Cook

"""

__version__ = "1.0.0"
__author__ = "Jack Kirby Cook"
__all__ = []
__copyright__ = "Copyright 2020, Jack Kirby Cook"
__license__ = ""


#class Housing(ntuple('Housing', 'unit sqftcost geography crimes schools space community proximity quality')):     
#    __stringformat = 'Housing|{unit} with {sqft}SQFT in {geography} builtin {year}|${rent:.0f}/MO Rent|${price:.0f} Purchase' 
#    __concepts = {}    
#    def __str__(self): 
#        unit = self.__concepts['unit'][self.unit] if 'unit' in self.__concepts.keys() else self.unit
#        content = dict(sqft=self.sqft, year=self.year, geography=str(self.geography), rent=self.rentercost, price=self.price)
#        return self.__stringformat.format(unit=unit, **content)
#    
#    @classmethod
#    def factory(cls, *args, **kwargs): 
#        cls.__concepts = kwargs.get('concepts', cls.__concepts)    
#        cls.__stringformat = kwargs.get('stringformat', cls.__stringformat)    
#
#    __instances = {} 
#    __count = 0
#    def __new__(cls, *args, **kwargs):
#        instance = super().__new__(cls, [kwargs[field] for field in cls._fields])
#        if hash(instance) in cls.__instances: 
#            cls.__instances[hash(instance)].count += 1
#            return cls.__instances[hash(instance)]
#        else:
#            instance.__count += 1
#            cls.__instances[hash(instance)] = instance
#            return instance
#        
#    def __init__(self, sqftprice, sqftrent,  *args, rentalrate, **kwargs):
#        assert 0 < rentalrate < 1
#        self.__sqftrent, self.__sqftprice = sqftrent, sqftprice
#        self.__rentalrate, self.__ownerrate = rentalrate, property(lambda: 1 - self.__rentalrate)
#        
#    def todict(self): return self._asdict()
#    def __getitem__(self, key): return self.todict()[key]    
#    def __hash__(self): pass
#
#    def __ne__(self, other): return not self.__eq__(other)
#    def __eq__(self, other):
#        assert isinstance(other, type(self))
#        return all([getattr(other, field) == getattr(self, field) for field in self._fields])
#    
#    @property
#    def count(self): return self.__count     
#    @property
#    def rentercount(self): return math.floor(self.__count * self.__rentalrate)
#    @property
#    def ownercount(self): return math.ceil(self.__count * self.__ownerrate)
#    
#    @property
#    def geoID(self): return self.geography.geoID    
#    @property
#    def year(self): return self.quality.yearbuilt
#    @property
#    def sqft(self): return self.space.sqft
#    
#    @property
#    def price(self): return self.__sqftprice * self.sqft      
#    @property
#    def ownercost(self): return self.__sqftcost * self.sqft    
#    @property
#    def rentercost(self): return self.__sqftrent * self.sqft
#
#    def __call__(self, duration_months, *args, pricerate, rentrate, **kwargs): 
#        self.__sqftrent = self.__sqftrent * pow(1 + pricerate, duration_months)
#        self.__sqftprice = self.__sqftprice * pow(1 + rentrate, duration_months)
#        return self





