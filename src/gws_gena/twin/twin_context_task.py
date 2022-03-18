# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      JSONDict, ResourceExporter, ResourceImporter, StrParam,
                      exporter_decorator, importer_decorator)

from .twin_context import TwinContext

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("TwinContextImporter", human_name="Twin context importer", source_type=File,
                    target_type=TwinContext, supported_extensions=[".json"])
class TwinContextImporter(ResourceImporter):
    config_specs: ConfigSpecs={
        'file_format': StrParam(allowed_values=[".json"], default_value=".json", short_description="File format")
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[TwinContext]) -> TwinContext:
        """
        Import from a repository

        :returns: the imported cotnext
        :rtype: TwinContext
        """

        file_format = params.get_value("file_format", ".json")
        if file_format in [".json"]:
            with open(file.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise BadRequestException("Invalid file format. A .json file is required.")

        return target_type.loads(data)

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("TwinContextExporter", human_name="Twin context exporter", source_type=TwinContext, target_type=File)
class TwinContextExporter(ResourceExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value="context", short_description="File name (without extension)"),
        'file_format': StrParam(
            allowed_values=[".json"], default_value=".json",
            short_description="File format.")}

    async def export_to_path(self, resource: TwinContext, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "context")
        file_format = params.get_value("file_format", ".json")
        file_path = os.path.join(dest_dir, file_name+file_format)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource.dumps(), f)

        return target_type(path=file_path)
