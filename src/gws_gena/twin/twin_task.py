import json
import os

from gws_core import (
    BadRequestException,
    ConfigParams,
    ConfigSpecs,
    File,
    FileHelper,
    ResourceExporter,
    ResourceImporter,
    StrParam,
    TypingStyle,
    exporter_decorator,
    importer_decorator,
)

from .twin import Twin

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(
    "TwinImporter",
    human_name="Twin importer",
    short_description="Import a digital twin of cell metabolism",
    source_type=File,
    target_type=Twin,
    supported_extensions=["json"],
    style=TypingStyle.material_icon(
        material_icon_name="cloud_download", background_color="#d9d9d9"
    ),
)
class TwinImporter(ResourceImporter):
    """TwinImporter

    Import a digital twin of cell metabolism
    """

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "file_format": StrParam(
                allowed_values=["json"], default_value="json", short_description="File format"
            )
        }
    )

    def import_from_path(self, file: File, params: ConfigParams, target_type: type[Twin]) -> Twin:
        """
        Import a twin from a repository

        :param file_path: The source file path
        :type file_path: str
        :returns: the tiwin
        :rtype: Twin
        """

        twin: Twin
        file_format = FileHelper.normalize_extension(params.get_value("file_format", "json"))
        if file_format == "json":
            with open(file.path, encoding="utf-8") as fp:
                try:
                    data = json.load(fp)
                except Exception as err:
                    raise BadRequestException(f"Cannot load JSON file {file.path}") from err
                if data.get("networks"):
                    # is a raw dump twin
                    twin = target_type.loads(data)
                elif data.get("twin"):
                    # is gws resource
                    twin = target_type.loads(data["twin"])
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


@exporter_decorator(
    "TwinExporter",
    human_name="Twin exporter",
    short_description="Export a digital twin of cell metabolism",
    source_type=Twin,
    target_type=File,
    style=TypingStyle.material_icon(material_icon_name="cloud_upload", background_color="#d9d9d9"),
)
class TwinExporter(ResourceExporter):
    """TwinExporter

    Export a digital twin of cell metabolism
    """

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "file_name": StrParam(
                default_value="twin", short_description="File name (without extension)"
            ),
            "file_format": StrParam(
                allowed_values=["json"], default_value="json", short_description="File format."
            ),
        }
    )

    def export_to_path(
        self, resource: Twin, dest_dir: str, params: ConfigParams, target_type: type[File]
    ) -> File:
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "twin")
        file_format = FileHelper.normalize_extension(params.get_value("file_format", "json"))
        file_path = os.path.join(dest_dir, file_name + "." + file_format)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource.dumps(deep=True), f)

        return target_type(path=file_path)
