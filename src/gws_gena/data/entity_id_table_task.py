# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      ListParam, StrParam, TableExporter, TableImporter,
                      exporter_decorator, importer_decorator)

from .entity_id_table import EntityIDTable, EntityIDTableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EntityIDTableImporter", human_name="EntityIDTable importer", source_type=EntityIDTableFile,
                    target_type=EntityIDTable)
class EntityIDTableImporter(TableImporter):
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
                f"Cannot import Table. No ids found (no column with name '{id_column}')")

        csv_table.id_column = id_column
        return csv_table


# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("EntityIDTableExporter", human_name="EntityIDTable exporter", source_type=EntityIDTable,
                    target_type=EntityIDTableFile)
class EntityIDTableExporter(TableExporter):
    pass
