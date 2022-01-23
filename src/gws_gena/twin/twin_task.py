# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      ResourceExporter, ResourceImporter, StrParam,
                      exporter_decorator, importer_decorator)

from .twin import Twin

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("TwinImporter", human_name="Twin importer", source_type=File, target_type=Twin)
class TwinImporter(ResourceImporter):
    config_specs: ConfigSpecs = {
        'file_format': StrParam(allowed_values=[".json"], default_value=".json", short_description="File format")
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Twin]) -> Twin:
        """
        Import a twin from a repository

        :param file_path: The source file path
        :type file_path: str
        :returns: the tiwin
        :rtype: Twin
        """

        twin: Network
        file_format = params.get_value("file_format", ".json")
        if file_format == ".json":
            with open(file_path, 'r') as fp:
                try:
                    _json = json.load(fp)
                except Exception as _:
                    raise BadRequestException(f"Cannot load JSON file {file_path}")
                if _json.get("networks"):
                    # is a raw dump twin
                    twin = target_type.loads(_json)
                elif _json.get("twin"):
                    # is gws resource
                    twin = target_type.loads(_json["twin"])
                else:
                    raise BadRequestException("Invalid twin data")
        else:
            raise BadRequestException("Invalid file format")
        return twin

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("TwinExporter", human_name="Twin exporter", source_type=Twin, target_type=File)
class TwinExporter(ResourceExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value="twin", short_description="File name (without extension)"),
        'file_format': StrParam(
            allowed_values=[".json"], default_value=".json",
            short_description="File format.")}

    async def export_to_path(self, resource: Twin, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "twin")
        file_format = params.get_value("file_format", ".json")
        file_path = os.path.join(dest_dir, file_name+file_format)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource.dumps(), f)

        return target_type(path=file_path)
