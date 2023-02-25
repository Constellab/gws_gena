# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Type

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, File, ResourceImporter, importer_decorator)

from ..network import Network


@importer_decorator("NetworkImporter", human_name="Network importer", source_type=File,
                    target_type=Network, supported_extensions=["json"])
class NetworkImporter(ResourceImporter):
    """ NetworkImporter """
    config_specs: ConfigSpecs = {
        "translate_ids":
        BoolParam(
            human_name="Translate all ids",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="If possible, translate all (compound and reaction) (recommended)"),
        "replace_unknown_compartments":
        BoolParam(
            human_name="Set default compartment as others",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set default compartment as others"),
        "skip_orphans":
        BoolParam(
            human_name="skip orphans compounds",
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to skip orphan compounds"),
    }

    async def import_from_path(self, source: File, params: ConfigParams, target_type: Type[Network]) -> Network:
        """
        Import a network from a repository

        :param source: The source file
        :type source: File
        :returns: the parsed data
        :rtype: any
        """

        net: Network
        translate_ids = params.get_value("translate_ids", False)
        skip_orphans = params.get_value("skip_orphans", False)
        replace_unknown_compartments = params.get_value("replace_unknown_compartments", False)
        with open(source.path, 'r', encoding="utf-8") as fp:
            try:
                data = json.load(fp)
            except Exception as err:
                raise BadRequestException(f"Cannot load JSON file {source.path}.") from err

            if data.get("reactions"):
                # is an unknown dump network (e.g. BiGG database, classical bioinformatics exchange files)
                net = Network.loads(
                    data,
                    skip_orphans=skip_orphans,
                    translate_ids=translate_ids,
                    replace_unknown_compartments=replace_unknown_compartments
                )
            elif data.get("network"):
                # is gws resource
                net = Network.loads(
                    data["network"],
                    skip_orphans=skip_orphans,
                    translate_ids=translate_ids,
                    replace_unknown_compartments=replace_unknown_compartments
                )
            elif data.get("data", {}).get("network"):
                # is gws old resource [RETRO COMPATIBILTY]
                # TODO: will be deprecated in the future
                net = Network.loads(
                    data["data"]["network"],
                    skip_orphans=skip_orphans,
                    translate_ids=translate_ids,
                    replace_unknown_compartments=replace_unknown_compartments
                )
            else:
                raise BadRequestException("Invalid network data")

        return net
