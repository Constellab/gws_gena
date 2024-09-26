
import os
from typing import Type

from gws_core import ( ConfigParams, ConfigSpecs, File,
                      FileHelper, ResourceExporter, StrParam,
                      exporter_decorator, TypingStyle)
from cobra.io import save_json_model
from ..network_cobra import NetworkCobra


@exporter_decorator(unique_name="NetworkExporterV2", human_name="Network exporter V2", source_type=NetworkCobra,
                    target_type=File,
                    style=TypingStyle.material_icon(material_icon_name="cloud_upload", background_color="#d9d9d9"))
class NetworkExporterV2(ResourceExporter):
    ALLOWED_FILE_FORMATS = ["json"]
    DEFAULT_FILE_FORMAT = "json"
    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value="network", short_description="File name (without extension)"),
        'file_format':
        StrParam(
            allowed_values=ALLOWED_FILE_FORMATS,
            default_value=DEFAULT_FILE_FORMAT,
            short_description="File format")}

    def export_to_path(self, resource: NetworkCobra, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        """
        Export the network to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        file_name = params.get_value("file_name", resource.name or "network")
        file_format = FileHelper.clean_extension(params.get_value("file_format", "json"))
        file_path = os.path.join(dest_dir, file_name + '.' + file_format)

        model = resource.get_cobra_model()
        save_json_model(model, file_path)

        return target_type(path=file_path)
