

from gws_core import BadRequestException, SerializableObjectJson

from ..measure import Measure
from ..typing.context_typing import ContextDict


class ContextData(SerializableObjectJson):
    """
    Context class

    A network `Context` is a resource object used to contextualize metabolic `Network` and create digital twin of cell metaolbism.
    """

    DEFAULT_NAME = "context"
    FLATTENING_DELIMITER = ":"

    name: str = None
    reaction_data: dict[str, Measure] = None
    compound_data: dict[str, Measure] = None

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME
            self.reaction_data = {}
            self.compound_data = {}

    def serialize(self) -> ContextDict:
        """
        Serialize
        """

        return self.dumps()

    @ classmethod
    def deserialize(cls, data: dict[str, dict]) -> 'ContextData':
        """ Deserialize """
        if data is None:
            return {}

        return cls.loads(data)

    # =========================== CLASS LOGIC ===========================

    # -- A --

    def add_reaction_data(self, measure: Measure):
        """ Add a reaction data """
        if measure.id in self.reaction_data:
            raise BadRequestException("Reaction data duplicate")
        self.reaction_data[measure.id] = measure

    def add_compound_data(self, measure: Measure):
        """ Add a compound data """
        if measure.id in self.compound_data:
            raise BadRequestException("Compound data duplicate")
        self.compound_data[measure.id] = measure

    # -- C --

    def copy(self) -> 'ContextData':
        """ Copy the context """
        ctx_data = ContextData()
        ctx_data.name = self.name
        ctx_data.reaction_data = {k: v.copy() for k, v in self.reaction_data.items()}
        ctx_data.compound_data = {k: v.copy() for k, v in self.compound_data.items()}
        return ctx_data

    # -- B --

    # -- D --

    def dumps(self) -> dict:
        """ Dumps the context data """
        data = {
            "name": self.name,
            "reaction_data": [],
            "compound_data": []
        }

        for measure in self.compound_data.values():
            data["compound_data"].append(measure.dumps())

        for measure in self.reaction_data.values():
            data["reaction_data"].append(measure.dumps())

        return data

    # -- E --

    # -- G --

    def get_reaction_data_ids(self) -> list[str]:
        """ Get the ids of the measures """
        return list(self.reaction_data.keys())

    def get_compound_data_ids(self) -> list[str]:
        """ Get the ids of the measures """
        return list(self.compound_data.keys())

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
        if "measures" in data:
            # Deprecated.
            # Used for retro-compatiility
            # ToDo: To remove later
            for measure_dict in data.get("measures", {}):
                measure = Measure(measure_dict)
                ctx.add_reaction_data(measure)
        else:
            for measure_dict in data.get("reaction_data", {}):
                measure = Measure(measure_dict)
                ctx.add_reaction_data(measure)

            for measure_dict in data.get("compound_data", {}):
                measure = Measure(measure_dict)
                ctx.add_compound_data(measure)

        ctx.name = data.get("name", cls.DEFAULT_NAME)
        return ctx
