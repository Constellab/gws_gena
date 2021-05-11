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
# EC Number Datatable class
#
# ####################################################################

class ECData(CSVData):
    """ 
    Represents ec number data
        
    * The first column the a compound name (offical or user-defined name)
    * The next columns are:
      * ec_number: the list of ec numbers
      
    For example:
      
    ``` 
    -------------------------------------
    component           | ec_number  
    -------------------------------------
    PNEG_00964          | 1.4.1.2
    PNEG_02355          | 4.2.1.10
    -------------------------------------
    ```
    """
    
    EC_COLUMN_NAME = "ec_number"
    
    # -- E --
    
    @property
    def ec_column_name(self):
        return self.data.get('ec_column_name', self.EC_COLUMN_NAME)

    @ec_column_name.setter
    def ec_column_name(self, name):
        self.data['ec_column_name'] = name
    
    # -- G --
    
    def get_ec_numbers(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.ec_column_name, rtype)
    
    # -- I --

    @classmethod
    def _import(cls, *args, ec_column_name:str="ec_number", **kwargs) -> 'ECData':
        """ 
        Import from a repository
        

        :param ec_column_name: The name of the column containing the EC numbers
        :type ec_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed data
        :rtype: ECData
        """
        
        data = super()._import(*args, **kwargs)
        
        if not data.column_exists( ec_column_name ):
            raise Error("ECData", "_import", f"No ec numbers found (no column with name '{ec_column_name}')")
        
        data.ec_column_name = ec_column_name
        return data
    
# ####################################################################
#
# Importer class
#
# ####################################################################
    
class ECImporter(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {"data": ECData}
    config_specs = {
        **CSVImporter.config_specs,
        'ec_column_name': {"type": 'str', "default": ECData.EC_COLUMN_NAME, "description": "The ec number column name"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class ECExporter(CSVExporter):
    input_specs = {"data": ECData}
    output_specs = {'file' : File}
    config_specs = {
        **CSVExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class ECLoader(CSVLoader):
    input_specs = {}
    output_specs = {"data" : ECData}
    config_specs = {
        **CSVLoader.config_specs,
        'ec_column_name': {"type": 'str', "default": ECData.EC_COLUMN_NAME, "description": "The ec number column name"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class ECDumper(CSVDumper):
    input_specs = {"data" : ECData}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }