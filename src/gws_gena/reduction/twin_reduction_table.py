# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core import (BadRequestException, ConfigParams, File, ListParam,
                      StrParam, StrRField, Table, TableExporter, TableImporter,
                      export_to_path, exporter_decorator, import_from_path,
                      importer_decorator, resource_decorator, task_decorator)


@resource_decorator("TwinReductionTable",
                    human_name="TwinReductionTable",
                    short_description="Twin reduction table")
class TwinReductionTable(Table):
    """
    Represents a twin reduction table
    """

    # -- E --

    # -- F --

    # -- I --
    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'TwinReductionTable':
        table = super().select_by_row_indexes(indexes)
        table = TwinReductionTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'TwinReductionTable':
        table = super().select_by_column_indexes(indexes)
        table = TwinReductionTable(data=table.get_data())
        return table

    def select_by_row_name(self, name_regex: str) -> 'TwinReductionTable':
        table = super().select_by_row_name(name_regex)
        table = TwinReductionTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'TwinReductionTable':
        table = super().select_by_column_name(name_regex)
        table = TwinReductionTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("TwinReductionTableImporter", resource_type=TwinReductionTable)
class TwinReductionTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("BiomassTableExporter", resource_type=TwinReductionTable)
class TwinReductionTableExporter(TableExporter):
    pass
