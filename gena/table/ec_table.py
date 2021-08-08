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
# EC Number Datatable class
#
# ####################################################################

class ECTable(CSVData):
    """ 
    Represents ec number data table
        
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
    def _import(cls, *args, ec_column_name:str="ec_number", **kwargs) -> 'ECTable':
        """ 
        Import from a repository
        

        :param ec_column_name: The name of the column containing the EC numbers
        :type ec_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed data
        :rtype: ECTable
        """
        
        data = super()._import(*args, **kwargs)
        
        if not data.column_exists( ec_column_name ):
            raise BadRequestException(f"Cannot import CSVData. No ec numbers found (no column with name '{ec_column_name}')")
        
        data.ec_column_name = ec_column_name
        return data

# ####################################################################
#
# Importer class
#
# ####################################################################
    
class ECImporter(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {"data": ECTable}
    config_specs = {
        **CSVImporter.config_specs,
        'ec_column_name': {"type": 'str', "default": ECTable.EC_COLUMN_NAME, "description": "The ec number column name"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class ECExporter(CSVExporter):
    input_specs = {"data": ECTable}
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
    output_specs = {"data" : ECTable}
    config_specs = {
        **CSVLoader.config_specs,
        'ec_column_name': {"type": 'str', "default": ECTable.EC_COLUMN_NAME, "description": "The ec number column name"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class ECDumper(CSVDumper):
    input_specs = {"data" : ECTable}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }