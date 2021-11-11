# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BadRequestException, ConfigParams, File, StrParam,
                      StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)

# ####################################################################
#
# EC Number Datatable class
#
# ####################################################################

EC_TABLE_DEFAULT_EC_COLUMN_NAME = "ec_number"


@resource_decorator("ECTable",
                    human_name="ECTable",
                    short_description="CSV table of EC numbers")
class ECTable(Table):
    """
    Represents an ec number data table

    * The first column the a compound name (official or user-defined name)
    * The next columns are:
      * ec_number: the list of ec numbers

    For example:

    ```
    -------------------------------------
    component           | ec_number
    -------------------------------------
    PNEG_00964          | 1.4.1.2
    PNEG_02355          | 4.2.1.10
    -------------------------------------
    ```
    """

    DEFAULT_EC_COLUMN_NAME = EC_TABLE_DEFAULT_EC_COLUMN_NAME
    ec_column_name: str = StrRField(default_value=EC_TABLE_DEFAULT_EC_COLUMN_NAME)

    # -- E --

    # -- G --

    def get_ec_numbers(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.ec_column_name, rtype)

    # -- I --

    @classmethod
    @import_from_path(specs={
        **TableImporter.config_specs,
        'ec_column_name': StrParam(default_value=EC_TABLE_DEFAULT_EC_COLUMN_NAME, short_description="The ec number column name"),
    })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'ECTable':
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed EC data
        :rtype: ECTable
        """

        csv_table = super().import_from_path(file, params)
        ec_column_name = params.get_value("ec_column_name", cls.DEFAULT_EC_COLUMN_NAME)

        if not csv_table.column_exists(ec_column_name):
            raise BadRequestException(
                f"Cannot import Table. No ec numbers found (no column with name '{ec_column_name}')")

        csv_table.ec_column_name = ec_column_name
        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("ECTableImporter", resource_type=ECTable)
class ECTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("ECTableExporter", resource_type=ECTable)
class ECTableExporter(TableExporter):
    pass
