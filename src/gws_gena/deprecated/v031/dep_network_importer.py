# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Type

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, File, ResourceImporter, importer_decorator)

from ...network.network import Network


@importer_decorator("NetworkImporter", human_name="Network importer", source_type=File,
                    target_type=Network, supported_extensions=[".json"],
                    hide=True, deprecated_since='0.3.2', deprecated_message="Use current NetworkImporter")
class NetworkImporter_v031(ResourceImporter):
    config_specs: ConfigSpecs = {
        "loads_biota_info":
        BoolParam(
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to loads Biota DB info related to entities (slow) False otherwise (fast)."),
        "skip_bigg_exchange_reactions":
        BoolParam(
            default_value=True,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to skip `exchange reactions` when importing BiGG data files; False otherwise"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Network]) -> Network:
        """
        This task is no longer maintained
        """

        raise BadRequestException("This task is deprecated and deactivated.")
