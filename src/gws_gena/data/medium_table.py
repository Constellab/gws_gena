# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import resource_decorator, task_decorator, Table
from gws_core import BadRequestException
from gws_core import File, TableLoader, TableDumper, TableImporter, TableExporter, StrParam, StrRField

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################

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
    
    DEFAULT_CHEBI_COLUMN_NAME = "chebi_id"
    chebi_column_name: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN_NAME)

    # -- E --

    # -- F --
    
    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column_name, rtype)
    
    # -- I --

    @classmethod
    def import_from_path(cls, *args, chebi_column_name:str=None, **kwargs) -> 'MediumTable':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param chebi_column_name: The name of the column containing the CheBI IDs
        :type chebi_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed csv table
        :rtype: MediumTable
        """
        
        csv_table = super().import_from_path(*args, index_col=0, **kwargs)
        chebi_column_name = chebi_column_name or cls.DEFAULT_CHEBI_COLUMN_NAME

        if not csv_table.column_exists( chebi_column_name ):
            raise BadRequestException(f"Cannot import MediumTable. No chebi ids found (no column with name '{chebi_column_name}')")
        
        csv_table.chebi_column_name = chebi_column_name
        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################
    
@task_decorator("MediumImporter")
class MediumImporter(TableImporter):
    input_specs = {'file' : File}
    output_specs = {'data': MediumTable}
    config_specs = {
        **TableImporter.config_specs,
        'chebi_column_name': StrParam(default_value=MediumTable.DEFAULT_CHEBI_COLUMN_NAME, human_name="CheBI column name", short_description="The CheBI ID column name"),
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

@task_decorator("MediumExporter")
class MediumExporter(TableExporter):
    input_specs = {'data': MediumTable}
    output_specs = {'file' : File}
    config_specs = {
        **TableExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

@task_decorator("MediumLoader")
class MediumLoader(TableLoader):
    input_specs = {}
    output_specs = {'data' : MediumTable}
    config_specs = {
        **TableLoader.config_specs,
        'chebi_column_name': StrParam(default_value=MediumTable.DEFAULT_CHEBI_COLUMN_NAME, human_name="CheBI column name", short_description="The CheBI ID column name"),
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

@task_decorator("MediumDumper")
class MediumDumper(TableDumper):
    input_specs = {'data' : MediumTable}
    output_specs = {}
    config_specs = {
        **TableDumper.config_specs,
    }