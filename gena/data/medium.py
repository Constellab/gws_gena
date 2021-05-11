# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import List

from gws.logger import Error
from gws.model import Process, ResourceSet
from gws.file import File
from gws.csv import CSVData, CSVLoader, CSVDumper, CSVImporter, CSVExporter

# ####################################################################
#
# Medium Datatable class
#
# ####################################################################

class MediumData(CSVData):
    """ 
    Represents medium composition data
        
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
    
    CHEBI_COLUMN_NAME = "chebi_id"
    
    # -- E --
    
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
    def _import(cls, *args, chebi_column_name:str="chebi_id", **kwargs) -> 'MediumData':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param chebi_column_name: The name of the column containing the CheBI IDs
        :type chebi_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed data
        :rtype: MediumData
        """
        
        data = super()._import(*args, index_col=0, **kwargs)
        
        if not data.column_exists( chebi_column_name ):
            raise Error("MediumData", "_import", f"No chebi ids found (no column with name '{chebi_column_name}')")
        
        data.chebi_column_name = chebi_column_name
        return data
    
# ####################################################################
#
# Importer class
#
# ####################################################################
    
class MediumImporter(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {'data': MediumData}
    config_specs = {
        **CSVImporter.config_specs,
        'chebi_column_name': {"type": 'str', "default": MediumData.CHEBI_COLUMN_NAME, "description": "The CheBI ID column name"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class MediumExporter(CSVExporter):
    input_specs = {'data': MediumData}
    output_specs = {'file' : File}
    config_specs = {
        **CSVExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class MediumLoader(CSVLoader):
    input_specs = {}
    output_specs = {'data' : MediumData}
    config_specs = {
        **CSVLoader.config_specs,
        'chebi_column_name': {"type": 'str', "default": MediumData.CHEBI_COLUMN_NAME, "description": "The CheBI ID column name"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class MediumDumper(CSVDumper):
    input_specs = {'data' : MediumData}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }