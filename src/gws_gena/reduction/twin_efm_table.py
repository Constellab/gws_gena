
from gws_core import Table, resource_decorator, TypingStyle


@resource_decorator("TwinEFMTable",
                    human_name="Twin EFM table",
                    short_description="Elementary flux mode (EFM) table", hide=True,
                    style=TypingStyle.material_icon(material_icon_name='table_chart', background_color='#FC201D'))
class TwinEFMTable(Table):
    """
    Represents the table of elementary flux modes
    """

    pass
