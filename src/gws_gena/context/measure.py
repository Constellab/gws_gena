# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, StringHelper

from ..network.helper.slugify_helper import SlugifyHelper
from .typing.measure_typing import MeasureDict
from .variable import Variable


class Measure:
    """
    Measure class

    A `Measure` is an object representing a measurable flux. It could correspond to a single (or a sum of) `Variable(s)`.

    For instance:

    Let `v1` and `v2` be the fluxes carried by 2 metabolic reactions `R1` and `R2`.
    - If `v1` is experimentally mesurable, then `M1 = v1` will be a measure.
    - If `v1` and `v2` are experimentally undistinguishable but only the sum of `v1` and `v2` can be detected,
    then `M2 = v1 + v2` will be a measure.

    These measures are used to build `Context` objects for the analysis of digital twins of cell metabolism.
    """

    id: str = None
    name: str = None
    lower_bound: float = None
    upper_bound: float = None
    target: float = None
    confidence_score: float = None
    variables: List[Variable] = None

    FLATTENING_DELIMITER = ":"

    def __init__(self, dict_: MeasureDict = None):
        if dict_ is None:
            dict_ = {}
        else:
            self.id = dict_.get("id") or ""
            self.name = dict_.get("name") or ""
            self.lower_bound = dict_.get("lower_bound")
            self.upper_bound = dict_.get("upper_bound")
            self.target = dict_.get("target")
            self.confidence_score = dict_.get("confidence_score")
            self.variables = []
            var_data = dict_.get("variables")
            for data_ in var_data:
                self.variables.append(Variable(data_))

        if self.id:
            self.id = SlugifyHelper.slugify_id(self.id)
        else:
            self.id = self._generate_unique_id()

        if not self.variables:
            self.variables = []

    # -- A --

    def add_variable(self, variable: Variable):
        """ Add a variable """
        if not isinstance(variable, Variable):
            raise BadRequestException("The variable must an instance of Variable")
        self.variables.append(variable)

    def copy(self):
        """ Copyt the measure """

        meas = Measure()
        meas.id = self.id
        meas.name = self.name
        meas.lower_bound = self.lower_bound
        meas.upper_bound = self.upper_bound
        meas.target = self.target
        meas.confidence_score = self.confidence_score
        meas.variables = [v.copy() for v in self.variables]
        return meas

    def dumps(self):
        """ dumps """

        var_data = []
        for _var in self.variables:
            var_data.append(_var.dumps())

        data = {
            "id": self._format_id(self.id),
            "name": self.name,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "target": self.target,
            "confidence_score": self.confidence_score,
            "variables": var_data
        }

        return data

    @classmethod
    def _format_id(cls, id_str):
        return id_str.replace(cls.FLATTENING_DELIMITER, "_")

    @classmethod
    def _generate_unique_id(cls) -> str:
        _id = StringHelper.generate_random_chars(9)
        return SlugifyHelper.slugify_id(_id)
