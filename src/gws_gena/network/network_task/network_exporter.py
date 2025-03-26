
import json
import os
from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      FileHelper, ResourceExporter, StrParam, TypingStyle,
                      exporter_decorator)
from pandas import DataFrame

from ..network import Network


@exporter_decorator(unique_name="NetworkExporter", human_name="Network exporter", source_type=Network,
                    target_type=File,
                    style=TypingStyle.material_icon(material_icon_name="cloud_upload", background_color="#d9d9d9"))
class NetworkExporter(ResourceExporter):
    ALLOWED_FILE_FORMATS = ["json", "csv", "tsv", "txt", "xls", "xlsx"]
    DEFAULT_FILE_FORMAT = "json"
    config_specs: ConfigSpecs = ConfigSpecs({
        'file_name': StrParam(default_value="network", short_description="File name (without extension)"),
        'file_format':
        StrParam(
            allowed_values=ALLOWED_FILE_FORMATS,
            default_value=DEFAULT_FILE_FORMAT,
            short_description="File format")})

    def export_to_path(self, resource: Network, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        """
        Export the network to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        file_name = params.get_value("file_name", resource.name or "network")
        file_format = FileHelper.clean_extension(
            params.get_value("file_format", "json"))
        file_path = os.path.join(dest_dir, file_name + '.' + file_format)

        if file_format in ["xls", "xlsx"]:
            table: DataFrame = resource.to_dataframe()
            table.to_excel(file_path)
        else:
            with open(file_path, 'w', encoding="utf-8") as fp:
                if file_format == "json":
                    data = resource.dumps()
                    json.dump(data, fp)

                elif file_format in ["csv", "txt", "tsv"]:
                    fp.write(resource.to_csv())
                else:
                    raise BadRequestException(
                        f"Invalid file format. Valid file formats are {NetworkExporter.ALLOWED_FILE_FORMATS}")

        return target_type(path=file_path)
