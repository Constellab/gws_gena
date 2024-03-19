# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import  Table, resource_decorator, TypingStyle


@resource_decorator("TwinReductionTable",
                    human_name="Twin reduction table",
                    short_description="Twin reduction table", hide=True,
                    style=TypingStyle.material_icon(material_icon_name='table_chart', background_color='#DAB788'))
class TwinReductionTable(Table):
    """
    Represents a twin reduction table
    """

    pass
