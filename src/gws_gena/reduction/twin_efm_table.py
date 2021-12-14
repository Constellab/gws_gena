# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, ConfigParams, File, ListParam,
                      StrParam, StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)


@resource_decorator("TwinEFMTable",
                    human_name="TwinEFMTable",
                    short_description="Twin reduction table")
class TwinEFMTable(Table):
    """
    Represents the table of elementary flux modes
    """

    # -- E --

    # -- F --

    # -- I --
    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'TwinEFMTable':
        table = super().select_by_row_indexes(indexes)
        table = TwinEFMTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'TwinEFMTable':
        table = super().select_by_column_indexes(indexes)
        table = TwinEFMTable(data=table.get_data())
        return table

    def select_by_row_name(self, name_regex: str) -> 'TwinEFMTable':
        table = super().select_by_row_name(name_regex)
        table = TwinEFMTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'TwinEFMTable':
        table = super().select_by_column_name(name_regex)
        table = TwinEFMTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("TwinEFMTableImporter", resource_type=TwinEFMTable)
class TwinEFMTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("BiomassTableExporter", resource_type=TwinEFMTable)
class TwinEFMTableExporter(TableExporter):
    pass
