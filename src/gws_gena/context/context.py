# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core import (BadRequestException, Resource, SerializableRField,
                      StringHelper, StrRField, resource_decorator)

from .context_data.context_data import ContextData
from .measure import Measure


@resource_decorator("Context", human_name="Network context", short_description="Context of metabolic network")
class Context(Resource):
    """
    Context class

    A network `Context` is a resource object used to contextualize metabolic `Network` and create digital twin of cell metaolbism.
    """

    DEFAULT_NAME = "context"
    FLATTENING_DELIMITER = ":"

    context_data: Dict = SerializableRField(ContextData)

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME
            self.context_data = ContextData()

    # -- A --

    def add_measure(self, measure: Measure):
        """ Add a measure """
        self.context_data.add_measure(measure)

    # -- C --

    def copy(self) -> 'Context':
        """ Copy the context """
        ctx = Context()
        ctx.name = self.name
        ctx.context_data = self.context_data.copy()
        return ctx

    # -- B --

    # -- D --

    def dumps(self) -> dict:
        """ Dumps the context """
        return self.context_data.dumps()

    # -- E --

    # -- G --

    def get_measure_ids(self) -> List[str]:
        """ Get the ids of the meassures """
        return self.context_data.get_measure_ids()

    # -- F --

    @classmethod
    def _format_id(cls, _id) -> str:
        return _id.replace(cls.FLATTENING_DELIMITER, "_")

    # -- I --

    # -- L --

    @classmethod
    def loads(cls, data: dict) -> 'Context':
        """ Loads the context """
        ctx = Context()
        ctx.context_data = ContextData.loads(data)
        ctx.name = ctx.context_data.name
        return ctx

    # -- M --

    @property
    def measures(self):
        """ Get the liste of measures """
        return self.context_data.measures
