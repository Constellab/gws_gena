# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException, JSONDict, resource_decorator


@resource_decorator("KnockOutAnalysisResult")
class KnockOutAnalysisResult(JSONDict):
    pass
