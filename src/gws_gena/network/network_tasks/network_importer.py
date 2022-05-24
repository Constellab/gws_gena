# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Type

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, File, ResourceExporter, ResourceImporter,
                      StrParam, exporter_decorator, importer_decorator)

from ..network import Network


@importer_decorator("NetworkImporter_001", human_name="Network importer", source_type=File,
                    target_type=Network, supported_extensions=[".json"])
class NetworkImporter(ResourceImporter):
    config_specs: ConfigSpecs = {
        "skip_orphans":
        BoolParam(
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to remove orphan compounds; False to keep them"),
        "loads_biota_info":
        BoolParam(
            default_value=True,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to loads Biota DB info related to entities (slower) False otherwise (fast)."),
        "skip_bigg_exchange_reactions":
        BoolParam(
            default_value=True,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to skip `exchange reactions` when importing BiGG data files; False otherwise"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Network]) -> Network:
        """
        Import a network from a repository

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype: any
        """

        net: Network
        loads_biota_info = params.get_value("loads_biota_info", True)
        skip_bigg_exchange_reactions = params.get_value("skip_bigg_exchange_reactions", True)
        skip_orphans = params.get_value("skip_orphans", False)

        with open(file.path, 'r', encoding="utf-8") as fp:
            try:
                _json = json.load(fp)
            except Exception as err:
                raise BadRequestException(f"Cannot load JSON file {file.path}.") from err

            if _json.get("reactions"):
                # is an unknown dump network (e.g. BiGG database, classical bioinformatics exchange files)
                net = target_type.loads(
                    _json,
                    skip_bigg_exchange_reactions=skip_bigg_exchange_reactions,
                    loads_biota_info=loads_biota_info,
                    skip_orphans=skip_orphans)
            elif _json.get("network"):
                # is gws resource
                net = target_type.loads(
                    _json["network"],
                    skip_orphans=skip_orphans)
            elif _json.get("data", {}).get("network"):
                # is gws old resource [RETRO COMPATIBILTY]
                # TODO: will be deprecated in the future
                net = target_type.loads(
                    _json["data"]["network"],
                    skip_orphans=skip_orphans)
            else:
                raise BadRequestException("Invalid network data")

        return net
