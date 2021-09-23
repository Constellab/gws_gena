# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import resource_decorator, task_decorator, CSVTable
from gws_core import BadRequestException
from gws_core import File, CSVLoader, CSVDumper, CSVImporter, CSVExporter, StrParam, StrRField

# ####################################################################
#
# EC Number Datatable class
#
# ####################################################################

@resource_decorator("ECNumberTable", 
                    human_name="ECNumberTable", 
                    short_description="CSV table of enzyme classification (EC) numbers")
class ECNumberTable(CSVTable):
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
    
    DEFAULT_EC_COLUMN_NAME = "ec_number"
    ec_column_name: str = StrRField(default_value=DEFAULT_EC_COLUMN_NAME)

    # -- E --

    # -- G --
    
    def get_ec_numbers(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.ec_column_name, rtype)
    
    # -- I --

    @classmethod
    def import_from_path(cls, *args, ec_column_name:str=None, **kwargs) -> 'ECNumberTable':
        """ 
        Import from a repository
        

        :param ec_column_name: The name of the column containing the EC numbers
        :type ec_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed data
        :rtype: ECNumberTable
        """
        
        csv_table = super().import_from_path(*args, **kwargs)
        ec_column_name = ec_column_name or cls.DEFAULT_EC_COLUMN_NAME

        if not csv_table.column_exists( ec_column_name ):
            raise BadRequestException(f"Cannot import CSVTable. No ec numbers found (no column with name '{ec_column_name}')")
        
        csv_table.ec_column_name = ec_column_name
        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################
    
@task_decorator("ECNumberImporter")
class ECNumberImporter(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {"data": ECNumberTable}
    config_specs = {
        **CSVImporter.config_specs,
        'ec_column_name': StrParam(default_value=ECNumberTable.DEFAULT_EC_COLUMN_NAME, description="The ec number column name"),
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

@task_decorator("ECNumberExporter")
class ECNumberExporter(CSVExporter):
    input_specs = {"data": ECNumberTable}
    output_specs = {'file' : File}
    config_specs = {
        **CSVExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

@task_decorator("ECNumberLoader")
class ECNumberLoader(CSVLoader):
    input_specs = {}
    output_specs = {"data" : ECNumberTable}
    config_specs = {
        **CSVLoader.config_specs,
        'ec_column_name': StrParam(default_value=ECNumberTable.DEFAULT_EC_COLUMN_NAME, description="The ec number column name"),
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

@task_decorator("ECNumberDumper")
class ECNumberDumper(CSVDumper):
    input_specs = {"data" : ECNumberTable}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }