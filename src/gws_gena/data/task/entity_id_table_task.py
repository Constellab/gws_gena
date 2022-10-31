# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator)

from ..entity_id_table import EntityIDTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EntityIDTableImporter", human_name="Entity ID table importer",
                    target_type=EntityIDTable, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class EntityIDTableImporter(TableImporter):
    """
    EntityIDTableImporter class

    Allows to import a `csv` or `xls` file and create a `EntityIDTable` resource object.
    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'id_column': StrParam(default_value=EntityIDTable.DEFAULT_ID_COLUMN, short_description="The column containing the IDs entities"),
        'name_column': StrParam(optional=True, short_description="The column containing the names of the entities"),
        'id_type': StrParam(default_value="", allowed_values=["", "chebi", "rhea"], short_description="The expected ID type"),
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[EntityIDTable]) -> EntityIDTable:
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed ID data
        :rtype: EntityIDTable
        """

        params["index_column"] = None
        csv_table = await super().import_from_path(file, params, target_type)
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