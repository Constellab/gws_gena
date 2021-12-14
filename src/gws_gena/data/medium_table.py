# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, ConfigParams, File, ListParam,
                      StrParam, StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################

MEDIUM_TABLE_DEFAULT_CHEBI_COLUMN = "chebi_id"


@resource_decorator("MediumTable",
                    human_name="MediumTable",
                    short_description="CSV table of experimental medium culture composition")
class MediumTable(Table):
    """
    Represents medium composition data table

    * The first column the a compound name (offical or user-defined name)
    * The next columns are:
      * chebi_id: the list chebi ids

    For example:

    ```
    -------------------------------------
    component           | chebi_id
    -------------------------------------
    2-oxoglutarate      | CEHBI:16810
    H20                 | CHEBI:15377
    -------------------------------------
    ```
    """

    DEFAULT_CHEBI_COLUMN = MEDIUM_TABLE_DEFAULT_CHEBI_COLUMN
    chebi_column: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN)

    # -- E --

    # -- F --

    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column, rtype)

    # -- I --

    @classmethod
    @import_from_path(
        specs={**TableImporter.config_specs,
               'chebi_column':
               StrParam(
                   default_value=MEDIUM_TABLE_DEFAULT_CHEBI_COLUMN, human_name="CheBI column name",
                   short_description="The CheBI ID column name"),
               'index_columns':
               ListParam(
                   optional=True,
                   short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"), })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'MediumTable':
        """
        Import from a repository

        Additional parameters

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed medium table
        :rtype: MediumTable
        """

        index_columns = params.get_value("index_columns") or 0
        params["index_columns"] = index_columns
        csv_table = super().import_from_path(file, params)

        chebi_column = params.get_value("chebi_column", cls.DEFAULT_CHEBI_COLUMN)
        if not csv_table.column_exists(chebi_column):
            raise BadRequestException(
                f"Cannot import MediumTable. No chebi ids found (no column with name '{chebi_column}')")

        csv_table.chebi_column = chebi_column
        return csv_table

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'MediumTable':
        table = super().select_by_row_indexes(indexes)
        table = MediumTable(data=table.get_data())
        table.chebi_column = self.chebi_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'MediumTable':
        table = super().select_by_column_indexes(indexes)
        table = MediumTable(data=table.get_data())
        table.chebi_column = self.chebi_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'MediumTable':
        table = super().select_by_row_name(name_regex)
        table = MediumTable(data=table.get_data())
        table.chebi_column = self.chebi_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'MediumTable':
        table = super().select_by_column_name(name_regex)
        table = MediumTable(data=table.get_data())
        table.chebi_column = self.chebi_column
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MediumTableImporter", resource_type=MediumTable)
class MediumTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("MediumTableExporter", resource_type=MediumTable)
class MediumTableExporter(TableExporter):
    pass
