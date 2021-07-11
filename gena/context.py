# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import uuid
from typing import List, Dict
from pathlib import Path

from gws.logger import Error
from gws.resource import Resource
from gws.process import Process
from gws.utils import generate_random_chars, slugify
from gws.json import JSONImporter, JSONExporter, JSONLoader, JSONDumper
from gws.file import File

from .network import Network
from .data import FluxData

def slugify_id(_id):
    return slugify(_id, snakefy=True, to_lower=False)

# ####################################################################
#
# Variable class
#
# ####################################################################

class Variable:
    coefficient = None
    reference_id = None
    reference_type = None #reaction | ...
    REACTION_REFERENCE_TYPE = "reaction"
    METABOLITE_REFERENCE_TYPE = "metabolite"
    _allowed_ref_types = [ REACTION_REFERENCE_TYPE, METABOLITE_REFERENCE_TYPE ]
    
    def __init__( self, coefficient: float, reference_id: str, reference_type: str = "metabolite"):
        if not reference_type in self._allowed_ref_types:
            raise Error("gena.context.Variable", "__init__", "Invalid reference_type")
        self.coefficient = coefficient
        self.reference_id = reference_id
        self.reference_type = reference_type
        
    def to_json(self):
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
    """
    Measure class
    """

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
                 lower_bound: float = -1000.0, upper_bound: float = 1000.0):
        if id:
            self.id = id
        else:
            self.id = self.__generate_unique_id()
        self.id = slugify_id(self.id)
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
    
    def to_json(self):
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
            _json["variables"].append( variable.to_json() )
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
    """
    Context class
    """

    _measures: Dict[str, Measure] = None
    _flattening_delim = ":"
    
    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self._measures = {}
        if self.data:
            self.__build_from_dump(self.data["measures"])
        else:
            self.data = {
                'name': 'Context',
                'description': '',
                'measures': None
            }
 
    # -- A --
    
    def to_json(self, stringify=False, prettify=False):
        _json = super().to_json()
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
        if "data" in data:
            # it is a raw export of the model
            data = data["data"] 
        for _meas in data["measures"]:
            measure = Measure( \
                id = self._format(_meas["id"]), \
                name = _meas.get("name"), \
                target = _meas.get("target"), \
                confidence_score = _meas.get("confidence_score",1.0), \
                lower_bound = _meas.get("lower_bound",-1000.0), \
                upper_bound = _meas.get("upper_bound",1000.0) \
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
    
    def dumps(self) -> dict:
        _json = []
        for k in self._measures:
            _json.append( self._measures[k].to_json() )
        return _json
        
    # -- E --

    def _export(self, file_path: str, file_format:str = ".json", prettify: bool=False):
        """ 
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """
    
        with open(file_path, "w") as f:
            if prettify:
                json.dump(self.dumps(), f, indent=4)
            else:
                json.dump(self.dumps(), f)

    # -- G --
    
    def get_measure_ids(self) -> List[str]:
        _ids = []
        for k in self._measures:
            m = self._measures[k]
            _ids.append(m.id)
        return _ids

    # -- F --

    @classmethod
    def _format(cls, id) -> str:
        return id.replace(cls._flattening_delim,"_")
    
    @classmethod
    def from_json(cls, data: dict) -> 'Context':
        ctx = Context()
        ctx.__build_from_dump(data)
        ctx.data["measures"] = ctx.dumps()
        return ctx
    
    # -- I --

    @classmethod
    def _import(cls, file_path: str, file_format:str = ".json") -> 'Context':
        """ 
        Import from a repository
 
        :returns: the imported cotnext
        :rtype: Context
        """

        file_extension = Path(file_path).suffix
        if file_extension in [".json"] or file_format in [".json"]:
            with open(file_path, "r") as f:
                data = json.load(f)
        return cls.from_json(data)

    # -- M --
    
    @property
    def measures(self):
        return self._measures
                           
    # -- S --
    
    def save(self, *args, **kwargs):
        self.data["measures"] = self.dumps()
        return super().save(*args, **kwargs)
    

class ContextBuilder(Process):
    input_specs = { 'network': (Network,), 'flux_data': (FluxData,) }
    output_specs = { 'context': (Context,) }
    config_specs = { }
    
    async def task(self):
        ctx = Context()
        flux = self.input["flux_data"]
        net = self.input["network"]
        targets = flux.get_targets()
        ubounds = flux.get_upper_bounds()
        lbounds = flux.get_lower_bounds()
        scores = flux.get_confidence_scores()
        i = 0
        for ref_id in flux.row_names:
            ref = net.get_reaction_by_id(ref_id)
            ref_type = Variable.REACTION_REFERENCE_TYPE

            #if not ref:
            #    ref = net.get_compound_by_id(ref_id)
            #    ref_type = Variable.METABOLITE_REFERENCE_TYPE

            if not ref:
                raise Error("ContextBuilder", "task", f"No reference reaction found with id {ref_id}")
        
            if ubounds[i] < lbounds[i]:
                raise Error("ContextBuilder", "task", f"Flux {ref_id}: the lower bound must be greater than upper bound")
                
            if targets[i] < lbounds[i]:
                raise Error("ContextBuilder", "task", f"Flux {ref_id}: the target must be greater than lower bound")
                
            if targets[i] > ubounds[i]:
                raise Error("ContextBuilder", "task", f"Flux {ref_id}: the target must be smaller than upper bound")
            
            m = Measure(
                id = "measure_" + ref_id,
                target = float(targets[i]),
                upper_bound = float(ubounds[i]),
                lower_bound = float(lbounds[i]),
                confidence_score = float(scores[i])
            )
            v = Variable(
                coefficient = 1.0,
                reference_id = ref_id,
                reference_type = ref_type
            )
            m.add_variable(v)
            ctx.add_measure(m)
            i += 1
        self.output["context"] = ctx

# ####################################################################
#
# Importer class
#
# ####################################################################
    
class ContextImporter(JSONImporter):
    input_specs = {'file' : File}
    output_specs = {'data': Context}
    config_specs = {
        'file_format': {"type": str, "default": ".json", 'description': "File format"}
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class ContextExporter(JSONExporter):
    input_specs = {'data': Context}
    output_specs = {'file' : File}
    config_specs = {
        'file_name': {"type": str, "default": 'network.json', 'description': "Destination file name in the store"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }
    
# ####################################################################
#
# Loader class
#
# ####################################################################

class ContextLoader(JSONLoader):
    input_specs = {}
    output_specs = {'data' : Context}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Location of the file to import"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }
    
# ####################################################################
#
# Dumper class
#
# ####################################################################

class ContextDumper(JSONDumper):
    input_specs = {'data' : Context}
    output_specs = {}
    config_specs = {
        'file_path': {"type": str, "default": None, 'description': "Destination of the exported file"},
        'file_format': {"type": str, "default": ".json", 'description': "File format"},
    }