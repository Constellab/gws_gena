# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import BadRequestException, Table, resource_decorator


@resource_decorator("TwinReductionTable",
                    human_name="TwinReductionTable",
                    short_description="Twin reduction table")
class TwinReductionTable(Table):
    """
    Represents a twin reduction table
    """

    pass
