# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import copy
import json
import os
import uuid
from pathlib import Path
from typing import Dict, List, TypedDict

from gws_core import (BadRequestException, ConfigParams, DictRField, File,
                      Resource, ResourceExporter, ResourceImporter, StrParam,
                      StrRField, Utils, export_to_path, exporter_decorator,
                      import_from_path, importer_decorator, resource_decorator,
                      task_decorator)


def slugify_id(_id):
    return Utils.slugify(_id, snakefy=True, to_lower=False)

# ####################################################################
#
# Variable class
#
# ####################################################################


class Variable:
    coefficient = None
    reference_id = None
    reference_type = None  # reaction | ...
    REACTION_REFERENCE_TYPE = "reaction"
    METABOLITE_REFERENCE_TYPE = "metabolite"
    _allowed_ref_types = [REACTION_REFERENCE_TYPE, METABOLITE_REFERENCE_TYPE]

    def __init__(self, coefficient: float, reference_id: str, reference_type: str = "metabolite"):
        if not reference_type in self._allowed_ref_types:
            raise BadRequestException("Invalid reference_type")
        self.coefficient = coefficient
        self.reference_id = reference_id
        self.reference_type = reference_type

    def copy(self):
        var = Variable(
            self.coefficient,
            self.reference_id,
            self.reference_type
        )
        return var

    def dumps(self):
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
    _ids = []
    _flattening_delim = ":"

    def __init__(self, id: str = None, name: str = "",
                 target: float = None, confidence_score: float = 1.0,
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
            raise BadRequestException("The variable must an instance of Variable")
        self._variables.append(variable)

    def copy(self):
        meas = Measure()
        meas.id = self.id
        meas.name = self.name
        meas.lower_bound = self.lower_bound
        meas.upper_bound = self.upper_bound
        meas.target = self.target
        meas.confidence_score = self.confidence_score
        meas._variables = [v.copy() for v in self._variables]
        meas._flattening_delim = self._flattening_delim
        meas._ids = copy.deepcopy(self._ids)
        return meas

    def dumps(self):
        _json = {
            "id": self._format(self.id),
            "name": self.name,
            "variables": [],
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "target": self.target,
            "confidence_score": self.confidence_score
        }
        for variable in self._variables:
            _json["variables"].append(variable.dumps())
        return _json

    @classmethod
    def _format(cls, id):
        return id.replace(cls._flattening_delim, "_")

    @classmethod
    def __generate_unique_id(cls):
        while True:
            id = Utils.generate_random_chars(9)
            if not id in cls._ids:
                cls._ids.append(id)
                return id

    # -- V --

    @property
    def variables(self):
        return self._variables

# ####################################################################
#
# TwinContext class
#
# ####################################################################


TwinContextDict = TypedDict("TwinContextDict", {
    "name": str,
    "measures": list,
})


@resource_decorator("TwinContext")
class TwinContext(Resource):
    """
    TwinContext class
    """
    DEFAULT_NAME = "context"

    name: str = StrRField()
    description: str = StrRField()
    measures: Dict[str, Measure] = DictRField()

    _flattening_delim = ":"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.measures = {}

    # -- A --

    def add_measure(self, measure: Measure):
        if measure.id in self.measures:
            raise BadRequestException("Measure duplicate")
        self.measures[measure.id] = measure

    # -- C --

    def copy(self) -> 'TwinContext':
        ctx = TwinContext()
        ctx.name = self.name
        ctx.description = self.description
        ctx._flattening_delim = self._flattening_delim
        ctx.measures = {k: self.measures[k].copy() for k in self.measures}
        return ctx

    # -- B --

    # -- D --

    def dumps(self) -> dict:
        _json = {"measures": []}
        for k in self.measures:
            _json["measures"].append(self.measures[k].dumps())
        return _json

    # -- E --

    @export_to_path(specs={
        'file_name': StrParam(default_value="context.json", short_description="File name"),
        # 'file_format': StrParam(default_value=".json", short_description="File format"),
    })
    def export_to_path(self, dest_dir: str, params: ConfigParams):
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "context.json")
        #file_format = params.get_value("file_format", ".json")
        file_path = os.path.join(dest_dir, file_name)
        with open(file_path, "w") as f:
            json.dump(self.dumps(), f)

    # -- G --

    def get_measure_ids(self) -> List[str]:
        _ids = []
        for k in self.measures:
            m = self.measures[k]
            _ids.append(m.id)
        return _ids

    # -- F --

    @classmethod
    def _format(cls, id) -> str:
        return id.replace(cls._flattening_delim, "_")

    # -- I --

    @classmethod
    @import_from_path(specs={
        'file_format': StrParam(default_value=".json", short_description="File format"),
    })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'TwinContext':
        """
        Import from a repository

        :returns: the imported cotnext
        :rtype: TwinContext
        """

        file_format = params.get_value("file_format", ".json")
        file_extension = Path(file.path).suffix or file_format
        file_extension = Path(file.path).suffix
        if file_extension in [".json"] or file_format in [".json"]:
            with open(file.path, "r") as f:
                data = json.load(f)
        return cls.loads(data)

    # -- L --

    @classmethod
    def loads(cls, data: dict) -> 'TwinContext':
        ctx = cls()
        for _meas in data["measures"]:
            measure = Measure(
                id=ctx._format(_meas["id"]),
                name=_meas.get("name"),
                target=_meas.get("target"),
                confidence_score=_meas.get("confidence_score", 1.0),
                lower_bound=_meas.get("lower_bound", -1000.0),
                upper_bound=_meas.get("upper_bound", 1000.0)
            )
            for _var in _meas["variables"]:
                variable = Variable(
                    coefficient=_var["coefficient"],
                    reference_id=_var["reference_id"],
                    reference_type=_var["reference_type"]
                )
                measure.add_variable(variable)
            ctx.add_measure(measure)

        ctx.name = cls._format(data.get("name", "TwinContext"))
        ctx.description = data.get("description", "")
        return ctx


# ####################################################################
#
# Importer class
#
# ####################################################################

@importer_decorator("ContextImporter", resource_type=TwinContext)
class ContextImporter(ResourceImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("ContextExporter", resource_type=TwinContext)
class ContextExporter(ResourceExporter):
    pass
