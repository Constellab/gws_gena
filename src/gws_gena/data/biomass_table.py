# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import resource_decorator, task_decorator, Table
from gws_core import BadRequestException
from gws_core import File, TableLoader, TableDumper, TableImporter, TableExporter, StrParam, StrRField

# ####################################################################
#
# Biomass Datatable class
#
# ####################################################################

@resource_decorator("BiomassTable", 
                    human_name="BiomassTable", 
                    short_description="CSV table describing biomass composition")
class BiomassTable(Table): 
    """ 
    Represents biomass data table
        
    * The first column the a compound name (offical or user-defined name)
    * The next columns are:
      * chebi_id: the chebi ids of componds of they are known (each chebi id must be prefixed by the keyword CHEBI:).
      * biomass: the biomass reaction data (described like a stoichiometric matrix)
      * other colums: these columns describe the reaction of the intermediate biomass constituents (described like a stoichiometric matrix)
    
    For example:
      
    ```  
    -------------------------------------------------------------------
    component               | chebi_id    | biomass      | protein
    -------------------------------------------------------------------
    biomass                 |             | 1            | 
    protein                 |             | -0,317663551 | 1
    DNA                     |             | -0,050537383 | 
    RNA                     |             | -0,025990654 | 
    Cofactors               |             | -0,021658879 | 
    Cell wall               |             | -0,115       | 
    Carbohydrates           |             | -0,202149533 | 
    Phospholipids           |             | -0,154266667 | 
    L-alanine zwitterion    | CHEBI:57972 |              | -0,587530055
    L-argininium(1+)        | CHEBI:32682 |              | -0,104025999
    L-asparagine zwitterion | CHEBI:58048 |              | -0,47552295
    L-aspartate(1-)         | CHEBI:29991 |              | -0,610918536
    L-cysteine zwitterion   | CHEBI:35235 |              | -0,475540207
    -------------------------------------------------------------------
    ```
    """
    
    DEFAULT_CHEBI_COLUMN_NAME = "chebi_id"
    DEFAULT_BIOMASS_COLUMN_NAME = "biomass"
    
    biomass_column_name: str = StrRField(default_value=DEFAULT_BIOMASS_COLUMN_NAME)
    chebi_column_name: str = StrRField(default_value=DEFAULT_CHEBI_COLUMN_NAME)

    # -- E --
    
    # -- F --
    
    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column_name, rtype)

    # -- I --

    @classmethod
    def import_from_path(cls, *args, chebi_column_name:str=None, biomass_column_name:str=None, **kwargs) -> 'BiomassTable':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param biomass_column_name: The name of the column containing the biomass equation
        :type biomass_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed table
        :rtype: BiomassTable
        """
        
        chebi_column_name = chebi_column_name or cls.DEFAULT_CHEBI_COLUMN_NAME
        biomass_column_name = biomass_column_name or cls.DEFAULT_BIOMASS_COLUMN_NAME

        csv_table = super().import_from_path(*args, index_col=0, **kwargs)
        if not csv_table.column_exists( chebi_column_name ):
            raise BadRequestException(f"Cannot import BiomassTable. No CheBI ID column found (no column with name '{chebi_column_name}')")
        
        if not csv_table.column_exists( biomass_column_name ):
            raise BadRequestException(f"Cannot import BiomassTable.  No biomass equation found (no column with name '{biomass_column_name}')")
        
        csv_table.biomass_column_name = biomass_column_name
        csv_table.chebi_column_name = chebi_column_name
        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################
    
@task_decorator("BiomassImporter")
class BiomassImporter(TableImporter):
    input_specs = {'file' : File}
    output_specs = {'data': BiomassTable}
    config_specs = {
        **TableImporter.config_specs,
        'chebi_column_name': StrParam(default_value=BiomassTable.DEFAULT_CHEBI_COLUMN_NAME, description="The CheBI ID column name"),
        'biomass_column_name': StrParam(default_value=BiomassTable.DEFAULT_BIOMASS_COLUMN_NAME, description="The biomass equation column name"),
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

@task_decorator("BiomassExporter")
class BiomassExporter(TableExporter):
    input_specs = {'data': BiomassTable}
    output_specs = {'file' : File}
    config_specs = {
        **TableExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

@task_decorator("BiomassLoader")
class BiomassLoader(TableLoader):
    input_specs = {}
    output_specs = {'data' : BiomassTable}
    config_specs = {
        **TableLoader.config_specs,
        'chebi_column_name': StrParam(default_value=BiomassTable.DEFAULT_CHEBI_COLUMN_NAME, description="The CheBI ID column name"),
        'biomass_column_name': StrParam(default_value=BiomassTable.DEFAULT_BIOMASS_COLUMN_NAME, description="The biomass equation column name"),
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

@task_decorator("BiomassDumper")
class BiomassDumper(TableDumper):
    input_specs = {'data' : BiomassTable}
    output_specs = {}
    config_specs = {
        **TableDumper.config_specs,
    }