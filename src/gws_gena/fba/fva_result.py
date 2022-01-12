# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import resource_decorator

from .fba_result import FBAResult


@resource_decorator("FVAResult", human_name="FVA", short_description="Flux variability Analysis Result")
class FVAResult(FBAResult):
    """
    FVAResult class
    """

    pass
