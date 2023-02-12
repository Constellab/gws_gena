# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core import (BadRequestException, ConfigParams, ConfigSpecs, File,
                      StrParam, Table, TableImporter, importer_decorator)

from ..ec_table import ECTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("ECTableImporter", human_name="EC number table importer",
                    target_type=ECTable, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class ECTableImporter(TableImporter):
    """
    ECTableImporter class

    Allows to import a `csv` or `xls` file and create a `ECTable` resource object.
    The `ECTable` is a table of EC numbers.
    """

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'ec_column':
        StrParam(
            default_value=ECTable.DEFAULT_EC_COLUMN,
            short_description="The name of the column containing the EC numbers"), }

    async def import_from_path(self, source: File, params: ConfigParams, target_type: Type[ECTable]) -> ECTable:
        """
        Import from a repository

        :param source: The source to import
        :type source: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed EC data
        :rtype: ECTable
        """

        params["index_column"] = None
        csv_table: ECTable = await super().import_from_path(source, params, target_type)
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
