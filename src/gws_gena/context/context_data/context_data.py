# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from gws_core import BadRequestException, SerializableObject

from ..measure import Measure
from ..typing.context_typing import ContextDict


class ContextData(SerializableObject):
    """
    Context class

    A network `Context` is a resource object used to contextualize metabolic `Network` and create digital twin of cell metaolbism.
    """

    DEFAULT_NAME = "context"
    FLATTENING_DELIMITER = ":"

    name: str = None
    measures: Dict[str, Measure] = None

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME
            self.measures = {}

    def serialize(self) -> ContextDict:
        """
        Serialize
        """

        return self.dumps()

    @ classmethod
    def deserialize(cls, data: Dict[str, dict]) -> 'ContextData':
        """ Deserialize """
        if data is None:
            return {}

        return cls.loads(data)

    # =========================== CLASS LOGIC ===========================

    # -- A --

    def add_measure(self, measure: Measure):
        """ Add a measure """
        if measure.id in self.measures:
            raise BadRequestException("Measure duplicate")
        self.measures[measure.id] = measure

    # -- C --

    def copy(self) -> 'ContextData':
        """ Copy the context """
        ctx = ContextData()
        ctx.name = self.name
        ctx.measures = {k: v.copy() for k, v in self.measures.items()}
        return ctx

    # -- B --

    # -- D --

    def dumps(self) -> dict:
        """ Dumps the context data """
        data = {
            "name": self.name,
            "measures": []
        }
        for measure in self.measures.values():
            data["measures"].append(measure.dumps())
        return data

    # -- E --

    # -- G --

    def get_measure_ids(self) -> List[str]:
        """ Get the ids of the meassures """
        return list(self.measures.keys())

    # -- F --

    @classmethod
    def _format_id(cls, _id) -> str:
        return _id.replace(cls.FLATTENING_DELIMITER, "_")

    # -- I --

    # -- L --

    @classmethod
    def loads(cls, data: dict) -> 'ContextData':
        """ Load a context data """
        ctx = cls()
        for measure_dict in data["measures"]:
            measure = Measure(measure_dict)
            ctx.add_measure(measure)

        ctx.name = data.get("name", cls.DEFAULT_NAME)
        return ctx
