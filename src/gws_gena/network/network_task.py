# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Type

from gws_core import (BadRequestException, BoolParam, ConfigParams,
                      ConfigSpecs, ResourceExporter, ResourceImporter,
                      StrParam, exporter_decorator, importer_decorator)
from pandas import DataFrame

from .network import Network
from .network_file import NetworkFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("NetworkImporter", human_name="Network importer", source_type=NetworkFile, target_type=Network)
class NetworkImporter(ResourceImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(
            allowed_values=[".json"],
            default_value=".json", short_description="File format"),
        "loads_biota_info":
        BoolParam(
            default_value=False,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to loads Biota DB info related to entities (slow) False otherwise (fast)."),
        "skip_bigg_exchange_reactions":
        BoolParam(
            default_value=True,
            visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="Set True to skip `exchange reactions` when importing BiGG data files; False otherwise")}

    async def import_from_path(self, file: NetworkFile, params: ConfigParams, target_type: Type[Network]) -> Network:
        """
        Import a network from a repository

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype: any
        """

        net: Network
        file_format = params.get_value("file_format", ".json")
        loads_biota_info = params.get_value("loads_biota_info", False)
        skip_bigg_exchange_reactions = params.get_value("skip_bigg_exchange_reactions", True)
        if file_format == ".json":
            with open(file.path, 'r', encoding="utf-8") as fp:
                try:
                    _json = json.load(fp)
                except Exception as err:
                    raise BadRequestException(f"Cannot load JSON file {file.path}.") from err

                if _json.get("reactions"):
                    # is an unknown dump network (e.g. BiGG database, classical bioinformatics exchange files)
                    net = target_type.loads(
                        _json, skip_bigg_exchange_reactions=skip_bigg_exchange_reactions,
                        loads_biota_info=loads_biota_info)
                elif _json.get("network"):
                    # is gws resource
                    net = target_type.loads(_json["network"])
                elif _json.get("data", {}).get("network"):
                    # is gws old resource [RETRO COMPATIBILTY]
                    # TODO: will be deprecated in the future
                    net = target_type.loads(_json["data"]["network"])
                else:
                    raise BadRequestException("Invalid network data")
        else:
            raise BadRequestException("Invalid file format. Only .json files can be imported.")
        return net

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="NetworkExporter", human_name="Network exporter", source_type=Network,
                    target_type=NetworkFile)
class NetworkExporter(ResourceExporter):
    ALLOWED_FILE_FORMATS = [".json", ".csv", ".tsv", ".txt", ".xls", ".xlsx"]
    DEFAULT_FILE_FORMAT = ".json"
    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value="network", short_description="File name (without extension)"),
        'file_format':
        StrParam(
            allowed_values=ALLOWED_FILE_FORMATS,
            default_value=DEFAULT_FILE_FORMAT,
            short_description="File format")}

    async def export_to_path(self, resource: Network, dest_dir: str, params: ConfigParams, target_type: Type[NetworkFile]) -> NetworkFile:
        """
        Export the network to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        file_name = params.get_value("file_name", resource.name or "network")
        file_format = params.get_value("file_format", ".json")
        file_path = os.path.join(dest_dir, file_name + file_format)
        with open(file_path, 'r', encoding="utf-8") as fp:
            if file_format == ".json":
                data = resource.dumps()
                json.dump(data, fp)
            elif file_format in [".xls", ".xlsx"]:
                table: DataFrame = resource.to_dataframe()
                table.to_excel(fp)
            elif file_format in [".csv", ".txt", ".tsv"]:
                fp.write(resource.to_csv())
            else:
                raise BadRequestException(
                    f"Invalid file format. Valid file formats are {NetworkExporter.ALLOWED_FILE_FORMATS}")

        return target_type(path=file_path)
