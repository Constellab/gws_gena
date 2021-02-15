# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List

from gws.logger import Error
from gws.model import Resource, ResourceSet
from gws.utils import generate_random_chars

# ####################################################################
#
# Variable class
#
# ####################################################################

class Variable:
    
    coefficient = None
    reference_id = None
    reference_type = None #reaction | ...
    
    _allowed_ref_types = ["reaction"]
    
    def __init__( self, coefficient: float, reference_id: str, reference_type: str = "reaction"):
        
        if not reference_type in self._allowed_ref_types:
            raise Error("gena.context.Variable", "__init__", "Invalid reference_type")
            
        self.coefficient = coefficient
        self.reference_id = reference_id
        self.reference_type = reference_type
        
    
    def as_json(self):
        _json = {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "coefficient": self.coefficient
        }
        return _json
    
# ####################################################################
#
# Measure class
#
# ####################################################################

class Measure:
    
    id: str = None
    name: str = None
    
    lower_bound: float = None
    upper_bound: float = None
    target: float = None
    confidence_score: float = None
    
    _variables: List[Variable] = None
    _flattening_delim = ":"
    _ids = []
    
    def __init__( self, id: str = None, name: str = "", \
                 target:float = None, confidence_score:float = 1.0, \
                 lower_bound: float = -1000, upper_bound: float = 1000):
        
        if id:
            self.id = id
        else:
            self.id = self.__generate_unique_id()

        self.name = name
        self.target = target
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.confidence_score = confidence_score
        self._variables = []
    
    # -- A --
    
    def add_variable(self, variable: Variable):
        if not isinstance(variable, Variable):
            raise Error("gena.context.Measure", "add_variable", "The variable must an instance of Variable")
            
        self._variables.append(variable)
    
    def as_json(self):
        
        _json = {
            "id": self._format(self.id),
            "name": self.name,
            "variables": [],
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "target": self.target,
            "confidence_score" : self.confidence_score
        }
        
        for variable in self._variables:
            _json["variables"].append( variable.as_json() )
        
        return _json
    
    @classmethod
    def _format(cls, id):
        return id.replace(cls._flattening_delim,"_")
    
    @classmethod
    def __generate_unique_id(cls):
        while True:
            id = generate_random_chars(9)
            if not id in cls._ids:
                cls._ids.append(id)
                return id
                    
    # -- V --
    
    @property
    def variables(self):
        return self._variables
    
# ####################################################################
#
# Context class
#
# ####################################################################

class Context(Resource):
    
    _measures: List[Measure] = None
    _flattening_delim = ":"
    
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
  
        self._measures = {}
        
        if self.data:
            self.__build_from_dump(self.data["measures"])
        else:
            self.data = {
                'title': 'Context',
                'description': '',
                'measures': None
            }
 
    # -- A --
    
    def as_json(self, stringify=False, prettify=False):
        _json = super().as_json()
        _json["data"]["measures"] = self.dumps()  #override to account for new updates
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json    
    
    def add_measure(self, measure: Measure):
        if measure.id in self._measures:
            raise Error("gena.context.Context", "add_measure", "Measure duplicate")
            
        self._measures[measure.id] = measure

    # -- B --
    
    def __build_from_dump(self, data: dict):
        for _meas in data["measures"]:
            measure = Measure( \
                id = self._format(_meas["id"]), \
                name = _meas.get("name"), \
                target = _meas.get("target"), \
                confidence_score = _meas.get("confidence_score",1.0), \
                lower_bound = _meas.get("lower_bound",1000), \
                upper_bound = _meas.get("upper_bound",1000) \
            )
            
            for _var in _meas["variables"]:
                variable = Variable( \
                    coefficient = _var["coefficient"], \
                    reference_id = _var["reference_id"], \
                    reference_type = _var["reference_type"] \
                )
                measure.add_variable(variable)
                              
            self.add_measure(measure)
            self.data["name"] = self._format( data.get("name","Context") )
            self.data["description"] = data.get("description","")
        
    # -- D -- 
    
    def dumps(self, stringify=False, prettify=False):
        _json = []
        for k in self._measures:
            _json.append( self._measures[k].as_json() )
        
        return _json
        
        
    # -- F --
    
    @classmethod
    def _format(cls, id):
        return id.replace(cls._flattening_delim,"_")
    
    @classmethod
    def from_json(cls, data: dict):
        ctx = Context()
        ctx.__build_from_dump(data)
        ctx.data["measures"] = ctx.dumps()
        return ctx
    
    # -- M --
    
    @property
    def measures(self):
        return self.data["measures"]
                           
    # -- S --
    
    def save(self, *args, **kwargs):
        self.data["measures"] = self.dumps()
        return super().save(*args, **kwargs)