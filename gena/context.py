# Core GWS app module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List

from gws.logger import Error
from gws.model import Resource

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
    _variables: List[Variable] = None
    lower_bound: float = None
    upper_bound: float = None
    target: float = None
    confidence_score: float = None
    
    def __init__( self, id: str = None, name: str = "", \
                 target:float = None, confidence_score:float = 1.0, \
                 lower_bound: float = -1000, upper_bound: float = 1000):
        
        if id:
            self.id = id
        else:
            self.id = str(uuid.uuid4())
            
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
            "id": self.id,
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
        
    def __init__( self, *args, twin: 'Twin' = None, **kwargs ):
        super().__init__( *args, **kwargs )
        
        if twin:
            self.add_to_twin(twin)
            
        self._measures = {}
        
        if self.data:
            self.__build_from_dump(self.data["measures"])
        else:
            self.data = {
                'measures': None
            }
 
    # -- A --
    
    #def as_json(self, stringify=False, prettify=False):
    #    _json = super().as_json(stringify, prettify)
    #    return _json
    
    
    def add_measure(self, measure: Measure):
        if measure.id in self._measures:
            raise Error("gena.context.Context", "add_measure", "Measure duplicate")
            
        self._measures[measure.id] = measure
        
    def add_to_twin( tw: 'Twin' = None ):
        tw.add_context(self)
        
    
    # -- B --
    
    def __build_from_dump(self, data: dict):
        for _meas in data["measures"]:
            measure = Measure( \
                id = _meas["id"], \
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
    
    # -- D -- 
    
    def dumps(self, stringify=False, prettify=False):
        _json = []
        
        for k in self._measures:
            _json.append( self._measures[k].as_json() )
        
        return _json
        
        
    # -- F --
    
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
    
    def save(*args, **kwargs):
        self.data["measures"] = self.dumps()
        return super().save(*args, **kwargs)