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

from .context import Context

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(
    "ContextImporter",
    human_name="Context importer",
    short_description="Metabolic context importer",
    source_type=File,
    target_type=Context,
    supported_extensions=["json"],
    style=TypingStyle.material_icon(material_icon_name="tune", background_color="#d9d9d9"),
)
class ContextImporter(ResourceImporter):
    """
    ContextImporter Task

    Import a metabolic context

    This Tasks also allows to import a context with multiple simulations. So if you have different values of target,lower_bound,upper_bound; set them as a list in your JSON File like this:
    {"id": "reaction1", "name": "", "lower_bound": [0.04,  0.045,  0.035], "upper_bound": [0.01, 0.008, -0.02], "target": [
        0.03, -0.003, 0.001], "confidence_score": [1, 1, 1], "variables": [{"reference_id": "Metabolite1", "coefficient": 1.0}]}
    """

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "file_format": StrParam(
                allowed_values=["json"], default_value="json", short_description="File format"
            )
        }
    )

    def import_from_path(
        self, file: File, params: ConfigParams, target_type: type[Context]
    ) -> Context:
        """
        Import from a repository

        :returns: the imported cotnext
        :rtype: Context
        """

        file_format = FileHelper.normalize_extension(params.get_value("file_format", "json"))
        if file_format in ["json"]:
            with open(file.path, encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise BadRequestException("Invalid file format. A .json file is required.")

        return target_type.loads(data)


# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(
    "ContextExporter",
    human_name="Context exporter",
    short_description="Metabolic context exporter",
    source_type=Context,
    target_type=File,
    style=TypingStyle.material_icon(material_icon_name="cloud_upload", background_color="#d9d9d9"),
)
class ContextExporter(ResourceExporter):
    """
    ContextExporter

    Exports a metabolic context
    """

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "file_name": StrParam(
                default_value="context", short_description="File name (without extension)"
            ),
            "file_format": StrParam(
                allowed_values=["json"], default_value="json", short_description="File format."
            ),
        }
    )

    def export_to_path(
        self, resource: Context, dest_dir: str, params: ConfigParams, target_type: type[File]
    ) -> File:
        """
        Export to a give repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "context")
        file_format = FileHelper.normalize_extension(params.get_value("file_format", "json"))
        file_path = os.path.join(dest_dir, file_name + "." + file_format)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(resource.dumps(), f)

        return target_type(path=file_path)
