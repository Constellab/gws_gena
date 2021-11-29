# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, ConfigParams, File, StrParam,
                      StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)

# ####################################################################
#
# ID Datatable class
#
# ####################################################################

ID_TABLE_DEFAULT_ID_COLUMN_NAME = "id"


@resource_decorator("IDTable",
                    human_name="IDTable",
                    short_description="CSV table IDs")
class IDTable(Table):
    """
    Represents and ID data table
    """

    DEFAULT_ID_COLUMN_NAME = ID_TABLE_DEFAULT_ID_COLUMN_NAME
    id_column_name: str = StrRField(default_value=ID_TABLE_DEFAULT_ID_COLUMN_NAME)

    # -- E --

    # -- G --

    def get_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.id_column_name, rtype)

    # -- I --

    @classmethod
    @import_from_path(specs={
        **TableImporter.config_specs,
        'id_column_name': StrParam(default_value=ID_TABLE_DEFAULT_ID_COLUMN_NAME, short_description="The name of the column containing the ID numbers"),
        'id_type': StrParam(default_value="", allowed_values=["", "chebi", "rhea"], short_description="The expected ID type"),
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
        id_column_name = params.get_value("id_column_name", cls.DEFAULT_ID_COLUMN_NAME)

        if not csv_table.column_exists(id_column_name):
            raise BadRequestException(
                f"Cannot import Table. No ids found (no column with name '{id_column_name}')")

        csv_table.id_column_name = id_column_name
        return csv_table

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'IDTable':
        table = super().select_by_row_indexes(indexes)
        table = IDTable(data=table.get_data())
        table.id_column_name = self.id_column_name
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'IDTable':
        table = super().select_by_column_indexes(indexes)
        table = IDTable(data=table.get_data())
        table.id_column_name = self.id_column_name
        return table

    def select_by_row_name(self, name_regex: str) -> 'IDTable':
        table = super().select_by_row_name(name_regex)
        table = IDTable(data=table.get_data())
        table.id_column_name = self.id_column_name
        return table

    def select_by_column_name(self, name_regex: str) -> 'IDTable':
        table = super().select_by_column_name(name_regex)
        table = IDTable(data=table.get_data())
        table.id_column_name = self.id_column_name
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
