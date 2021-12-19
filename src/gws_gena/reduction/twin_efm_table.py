# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, Table, resource_decorator


@resource_decorator("TwinEFMTable",
                    human_name="TwinEFMTable",
                    short_description="Twin reduction table")
class TwinEFMTable(Table):
    """
    Represents the table of elementary flux modes
    """

    pass
