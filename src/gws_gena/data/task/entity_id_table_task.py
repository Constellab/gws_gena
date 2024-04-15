
from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator, TypingStyle)

from ..entity_id_table import EntityIDTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EntityIDTableImporter", human_name="Entity ID table importer",
                    target_type=EntityIDTable, supported_extensions=Table.ALLOWED_FILE_FORMATS,
                    style=TypingStyle.material_icon(material_icon_name="cloud_download", background_color="#d9d9d9"))
class EntityIDTableImporter(TableImporter):
    """
    EntityIDTableImporter class

    Allows to import a `csv` or `xls` file and create a `EntityIDTable` resource object.

    Your File must have at least:
    - a column with the ID of the entity
    For example:

    | id           |  name                  |
    | -------------|------------------------|
    | CHEBI:57972  |  L-alanine             |
    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'id_column': StrParam(default_value=EntityIDTable.DEFAULT_ID_COLUMN, short_description="The column containing the IDs entities"),
        'name_column': StrParam(optional=True, short_description="The column containing the names of the entities"),
        'id_type': StrParam(default_value="", allowed_values=["", "chebi", "rhea"], short_description="The expected ID type"),
    }

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[EntityIDTable]) -> EntityIDTable:
        """
        Import from a repository

        :param source: The file to import
        :type source: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed ID data
        :rtype: EntityIDTable
        """

        params["index_column"] = None
        csv_table = super().import_from_path(source, params, target_type)
        id_column = params.get_value("id_column", EntityIDTable.DEFAULT_ID_COLUMN)

        if not csv_table.column_exists(id_column):
            raise BadRequestException(
                f"Cannot import the table. No column found with name '{id_column}'.")
        csv_table.id_column = id_column

        ids = csv_table.get_ids()
        if len(ids) == 0:
            raise BadRequestException(
                "Cannot import the table. The list of ids is empty.")

        unique_ids = list(set(ids))
        if len(ids) > len(unique_ids):
            duplicates = [elt for elt in ids if elt not in unique_ids]
            raise BadRequestException(
                f"Cannot import the table. The ids in the table must be unique. Duplicates are {duplicates}.")

        return csv_table
