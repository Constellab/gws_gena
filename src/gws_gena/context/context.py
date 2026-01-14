from gws_core import (
    ConfigParams,
    JSONView,
    Resource,
    TypingStyle,
    resource_decorator,
    view,
)

from .context_data.context_data import ContextData
from .measure import Measure


@resource_decorator(
    "Context",
    human_name="Network context",
    short_description="Context of metabolic network",
    style=TypingStyle.material_icon(material_icon_name="tune", background_color="#245678"),
)
class Context(Resource):
    """
    Context class

    A network `Context` is a resource object used to contextualize metabolic `Network` and create digital twin of cell metabolism.
    """

    DEFAULT_NAME = "context"
    FLATTENING_DELIMITER = ":"

    def __init__(self):
        super().__init__()
        if not self.name:
            self.name = self.DEFAULT_NAME
            self.context_data = ContextData()

    # -- A --

    def add_reaction_data(self, measure: Measure):
        """Add a reaction data"""
        self.context_data.add_reaction_data(measure)

    def add_compound_data(self, measure: Measure):
        """Add a compound data"""
        self.context_data.add_compound_data(measure)

    # -- C --

    def copy(self) -> "Context":
        """Copy the context"""
        ctx = Context()
        ctx.name = self.name
        ctx.context_data = self.context_data.copy()
        return ctx

    # -- B --

    # -- D --

    def dumps(self) -> dict:
        """Dumps the context"""
        return self.context_data.dumps()

    # -- E --

    # -- G --

    def get_reaction_ids(self) -> list[str]:
        """Get the ids of the reaction_data"""
        return self.context_data.get_reaction_data_ids()

    def get_compound_ids(self) -> list[str]:
        """Get the ids of the compound_data"""
        return self.context_data.get_compound_data_ids()

    # -- F --

    @classmethod
    def _format_id(cls, _id) -> str:
        return _id.replace(cls.FLATTENING_DELIMITER, "_")

    # -- I --

    # -- L --

    @classmethod
    def loads(cls, data: dict) -> "Context":
        """Loads the context"""
        ctx = Context()
        ctx.context_data = ContextData.loads(data)
        ctx.name = ctx.context_data.name
        return ctx

    # -- M --

    @property
    def reaction_data(self):
        """Get the list of reaction data"""
        return self.context_data.reaction_data

    @property
    def compound_data(self):
        """Get the list of compound data"""
        return self.context_data.compound_data

    # -- V --

    @view(
        view_type=JSONView,
        human_name="Show context",
        short_description="Show content as JSON",
        default_view=True,
    )
    def view_content_as_json(self, params: ConfigParams) -> JSONView:
        context_data = self.context_data
        data = context_data.dumps()
        return JSONView(data)
