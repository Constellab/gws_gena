# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (resource_decorator, task_decorator, Table, 
                    BadRequestException, ConfigParams,
                    import_from_path, export_to_path, importer_decorator, exporter_decorator,
                    File, TableImporter, TableExporter, StrParam, StrRField)

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################

MEDIUM_TABLE_DEFAULT_CHEBI_COLUMN_NAME = "chebi_id"

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
    
    DEFAULT_CHEBI_COLUMN_NAME = MEDIUM_TABLE_DEFAULT_CHEBI_COLUMN_NAME
    chebi_column_name: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN_NAME)

    # -- E --

    # -- F --
    
    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column_name, rtype)
    
    # -- I --

    @classmethod
    @import_from_path(specs = {
        **TableImporter.config_specs,
        'chebi_column_name': StrParam(default_value=MEDIUM_TABLE_DEFAULT_CHEBI_COLUMN_NAME, human_name="CheBI column name", short_description="The CheBI ID column name"),
    })
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

        chebi_column_name = params.get_value("chebi_column_name", cls.DEFAULT_CHEBI_COLUMN_NAME)
        if not csv_table.column_exists( chebi_column_name ):
            raise BadRequestException(f"Cannot import MediumTable. No chebi ids found (no column with name '{chebi_column_name}')")
        
        csv_table.chebi_column_name = chebi_column_name
        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################
    
@importer_decorator("MediumImporter", resource_type=MediumTable)
class MediumImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################

@exporter_decorator("MediumExporter", resource_type=MediumTable)
class MediumExporter(TableExporter):
    pass