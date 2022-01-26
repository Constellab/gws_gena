# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException, Table, resource_decorator


@resource_decorator("TwinReductionTable",
                    human_name="Twin reduction table",
                    short_description="Twin reduction table", hide=True)
class TwinReductionTable(Table):
    """
    Represents a twin reduction table
    """

    pass
