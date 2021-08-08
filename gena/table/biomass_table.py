# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.csv import CSVData
from gws.exception.bad_request_exception import BadRequestException
from gws.file import File
from gws.csv import CSVLoader, CSVDumper, CSVImporter, CSVExporter

# ####################################################################
#
# Biomass Datatable class
#
# ####################################################################

class BiomassTable(CSVData): 
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
    
    CHEBI_COLUMN_NAME = "chebi_id"
    BIOMASS_COLUMN_NAME = "biomass"
    
    # -- E --
    
    @property
    def biomass_column_name(self):
        return self.data.get('biomass_column_name', self.BIOMASS_COLUMN_NAME)

    @biomass_column_name.setter
    def biomass_column_name(self, name):
        self.data['biomass_column_name'] = name
        
    @property
    def chebi_column_name(self):
        return self.data.get('chebi_column_name', self.CHEBI_COLUMN_NAME)

    @chebi_column_name.setter
    def chebi_column_name(self, name):
        self.data['chebi_column_name'] = name
    
    # -- F --
    
    def get_chebi_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.chebi_column_name, rtype)

    # -- I --

    @classmethod
    def _import(cls, *args, chebi_column_name:str="chebi_id", biomass_column_name:str="biomass", **kwargs) -> 'BiomassTable':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param biomass_column_name: The name of the column containing the biomass equation
        :type biomass_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed data
        :rtype: BiomassTable
        """
        
        data = super()._import(*args, index_col=0, **kwargs)
        if not data.column_exists( chebi_column_name ):
            raise BadRequestException(f"Cannot import BiomassTable. No CheBI ID column found (no column with name '{chebi_column_name}')")
        
        if not data.column_exists( biomass_column_name ):
            raise BadRequestException(f"Cannot import BiomassTable.  No biomass equation found (no column with name '{biomass_column_name}')")
        
        data.biomass_column_name = biomass_column_name
        data.chebi_column_name = chebi_column_name
        return data

# ####################################################################
#
# Importer class
#
# ####################################################################
    
class BiomassImporter(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {'data': BiomassTable}
    config_specs = {
        **CSVImporter.config_specs,
        'chebi_column_name': {"type": 'str', "default": BiomassTable.CHEBI_COLUMN_NAME, "description": "The CheBI ID column name"},
        'biomass_column_name': {"type": 'str', "default": BiomassTable.BIOMASS_COLUMN_NAME, "description": "The biomass equation column name"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class BiomassExporter(CSVExporter):
    input_specs = {'data': BiomassTable}
    output_specs = {'file' : File}
    config_specs = {
        **CSVExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class BiomassLoader(CSVLoader):
    input_specs = {}
    output_specs = {'data' : BiomassTable}
    config_specs = {
        **CSVLoader.config_specs,
        'chebi_column_name': {"type": 'str', "default": BiomassTable.CHEBI_COLUMN_NAME, "description": "The CheBI ID column name"},
        'biomass_column_name': {"type": 'str', "default": BiomassTable.BIOMASS_COLUMN_NAME, "description": "The biomass equation column name"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class BiomassDumper(CSVDumper):
    input_specs = {'data' : BiomassTable}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }