# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import Table, resource_decorator, TypingStyle


@resource_decorator("TwinEFMTable",
                    human_name="Twin EFM table",
                    short_description="Elementary flux mode (EFM) table", hide=True,
                    style=TypingStyle.material_icon(material_icon_name='home', background_color='#FC201D'))
class TwinEFMTable(Table):
    """
    Represents the table of elementary flux modes
    """

    pass
