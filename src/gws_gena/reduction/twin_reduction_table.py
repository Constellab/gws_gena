from gws_core import Table, TypingStyle, resource_decorator


@resource_decorator(
    "TwinReductionTable",
    human_name="Twin reduction table",
    short_description="Twin reduction table",
    hide=True,
    style=TypingStyle.material_icon(material_icon_name="table_chart", background_color="#DAB788"),
)
class TwinReductionTable(Table):
    """
    Represents a twin reduction table
    """

    pass
