
from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator, TypingStyle)

from ..medium_table import MediumTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MediumTableImporter", human_name="Medium table importer",
                    short_description="Culture medium table importer", target_type=MediumTable,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS,
                    style=TypingStyle.material_icon(material_icon_name="cloud_download", background_color="#d9d9d9"))
class MediumTableImporter(TableImporter):
    """
    MediumTableImporter class

    Allows to import a `csv` or `xls` file and create a `MediumTable` object resource.
    The `MediumTable` is a table representing a culture medium composition.

    Your file must have:
    - a column with the compound name
    - a column with the chebi id

    For example:

    | entity              | chebi_id     |
    | --------------------|--------------|
    | 2-oxoglutarate      | CHEBI:16810  |
    | glutamine           | CHEBI:18050  |

    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'entity_column':
        StrParam(
            default_value=MediumTable.DEFAULT_ENTITY_COLUMN,
            human_name="The `entity` column name",
            short_description="The name of the column containing the entity names"),
        'chebi_column':
        StrParam(
            default_value=MediumTable.DEFAULT_CHEBI_COLUMN,
            human_name="The `chebi_id` column name",
            short_description="The name of the column containing the list of chebi ids")
    }

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[MediumTable]) -> MediumTable:
        """
        Import from a repository

        Additional parameters

        :param source: The file to import
        :type source: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed medium table
        :rtype: MediumTable
        """

        params["index_column"] = None
        csv_table = super().import_from_path(source, params, target_type)

        entity_column = params.get_value("entity_column", MediumTable.DEFAULT_ENTITY_COLUMN)
        chebi_column = params.get_value("chebi_column", MediumTable.DEFAULT_CHEBI_COLUMN)

        if not csv_table.column_exists(entity_column):
            raise BadRequestException(
                f"Cannot import MediumTable. No `entity` column found (no column with name '{entity_column}')")
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import MediumTable. No `chebi_id` column found (no column with name '{chebi_column}')")

        csv_table.entity_column = entity_column
        csv_table.chebi_column = chebi_column
        return csv_table
