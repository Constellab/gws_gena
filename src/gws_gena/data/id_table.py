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
# ID Datatable class
#
# ####################################################################

ID_TABLE_DEFAULT_NAME = "name"
ID_TABLE_DEFAULT_ID_COLUMN = "id"


@resource_decorator("IDTable",
                    human_name="IDTable",
                    short_description="CSV table IDs")
class IDTable(Table):
    """
    Represents and ID data table
    """

    DEFAULT_ID_COLUMN = ID_TABLE_DEFAULT_ID_COLUMN
    DEFAULT_NAME_COLUMN = ID_TABLE_DEFAULT_NAME
    id_column: str = StrRField(default_value=ID_TABLE_DEFAULT_ID_COLUMN)

    # -- E --

    # -- G --

    def get_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.id_column, rtype)

    # -- I --

    @classmethod
    @import_from_path(specs={
        **TableImporter.config_specs,
        'id_column': StrParam(default_value=ID_TABLE_DEFAULT_ID_COLUMN, short_description="The column containing the IDs entities"),
        'name_column': StrParam(optional=True, short_description="The column containing the names of the entities"),
        'id_type': StrParam(default_value="", allowed_values=["", "chebi", "rhea"], short_description="The expected ID type"),
        'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for CSV files"),
    })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'IDTable':
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed ID data
        :rtype: IDTable
        """

        csv_table = super().import_from_path(file, params)
        id_column = params.get_value("id_column", cls.DEFAULT_ID_COLUMN)

        if not csv_table.column_exists(id_column):
            raise BadRequestException(
                f"Cannot import Table. No ids found (no column with name '{id_column}')")

        csv_table.id_column = id_column
        return csv_table

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'IDTable':
        table = super().select_by_row_indexes(indexes)
        table = IDTable(data=table.get_data())
        table.id_column = self.id_column
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'IDTable':
        table = super().select_by_column_indexes(indexes)
        table = IDTable(data=table.get_data())
        table.id_column = self.id_column
        return table

    def select_by_row_name(self, name_regex: str) -> 'IDTable':
        table = super().select_by_row_name(name_regex)
        table = IDTable(data=table.get_data())
        table.id_column = self.id_column
        return table

    def select_by_column_name(self, name_regex: str) -> 'IDTable':
        table = super().select_by_column_name(name_regex)
        table = IDTable(data=table.get_data())
        table.id_column = self.id_column
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("IDTableImporter", resource_type=IDTable)
class IDTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("IDTableExporter", resource_type=IDTable)
class IDTableExporter(TableExporter):
    pass
