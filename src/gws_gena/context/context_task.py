# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      FileHelper, ResourceExporter, ResourceImporter, StrParam,
                      exporter_decorator, importer_decorator)

from .context import Context

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("ContextImporter", human_name="Context importer",
                    short_description="Metabolic context importer",
                    source_type=File, target_type=Context, supported_extensions=["json"])
class ContextImporter(ResourceImporter):
    """
    ContextImporter Task

    Import a metabolic context
    """

    config_specs: ConfigSpecs = {
        'file_format': StrParam(allowed_values=["json"], default_value="json", short_description="File format")
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Context]) -> Context:
        """
        Import from a repository

        :returns: the imported cotnext
        :rtype: Context
        """

        file_format = FileHelper.clean_extension(params.get_value("file_format", "json"))
        if file_format in ["json"]:
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


@exporter_decorator("ContextExporter", human_name="Context exporter",
                    short_description="Metabolic context exporter",
                    source_type=Context, target_type=File)
class ContextExporter(ResourceExporter):
    """
    ContextExporter

    Exports a metabolic context
    """

    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value="context", short_description="File name (without extension)"),
        'file_format': StrParam(
            allowed_values=["json"], default_value="json",
            short_description="File format.")}

    async def export_to_path(self, resource: Context, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "context")
        file_format = FileHelper.clean_extension(params.get_value("file_format", "json"))
        file_path = os.path.join(dest_dir, file_name+file_format)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource.dumps(), f)

        return target_type(path=file_path)
