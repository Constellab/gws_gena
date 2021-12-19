# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      ListParam, StrParam, TableExporter, TableImporter,
                      exporter_decorator, importer_decorator)

from .ec_table import ECTable, ECTableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("ECTableImporter", source_type=ECTableFile, target_type=ECTable)
class ECTableImporter(TableImporter):
    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'ec_column': StrParam(default_value=ECTable.DEFAULT_EC_COLUMN, short_description="The name of the column containing the EC numbers"),
        'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files")
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[ECTable]) -> ECTable:
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed EC data
        :rtype: ECTable
        """

        csv_table: ECTable = await super().import_from_path(file, params, target_type)

        print(csv_table)

        ec_column = params.get_value("ec_column", ECTable.DEFAULT_EC_COLUMN)

        if not csv_table.column_exists(ec_column):
            raise BadRequestException(
                f"Cannot import Table. No ec numbers found (no column with name '{ec_column}')")

        csv_table.ec_column = ec_column

        # clean ec data
        csv_table._data.replace(
            to_replace={ec_column: r"EC:"},
            value={ec_column: ""},
            regex=True,
            inplace=True
        )

        return csv_table


# ####################################################################
#
# Exporter class
#
# ####################################################################


@ exporter_decorator("ECTableExporter", source_type=ECTable, target_type=ECTableFile)
class ECTableExporter(TableExporter):
    pass
