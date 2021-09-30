# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import resource_decorator, task_decorator, Table
from gws_core import BadRequestException
from gws_core import File, TableLoader, TableDumper, TableImporter, TableExporter, StrParam, StrRField

# ####################################################################
#
# Flux Datatable class
#
# ####################################################################

@resource_decorator("FluxTable",
                    human_name="FluxTable", 
                    short_description="CSV table of experimental metabolic fluxes")
class FluxTable(Table):
    """ 
    Represents experimentally-measured (or user-defined) flux data table
        
    * The first column is the list of `reaction ids` and/or `ec numbers`. They uniquely identify each reaction of a network.
    * The next columns are:
      * target: value of flux measured experimentally (e.g. `mol/g DW/h`)
      * upper_bound: the upper bound of the flux (e.g. `mol/g DW/h`)
      * lower_bound: the lower bound of the flux (e.g. `mol/g DW/h`)
      * confidence_score: the confidence score of the flux
      
    For example:
      
    ```  
    ------------------------------------------------------------------------------------
    id                      | target    | lower_bound  | lower_bound  | confidence_score
    ------------------------------------------------------------------------------------
    RHEA_62620_1_11_1_24    | 0.234     | 0            | 1000         | 1.0
    6.3.1.2                 | -1.234    | -5           | 0            | 1.0
    ------------------------------------------------------------------------------------
    ```
    """
    
    DEFAULT_TARGET_COLUMN_NAME = "target"
    DEFAULT_UPPER_BOUND_COLUMN_NAME = "upper_bound"
    DEFAULT_LOWER_BOUND_COLUMN_NAME = "lower_bound"
    DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME = "confidence_score"
    
    confidence_score_column_name: str = StrRField(default_value=DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME)

    # -- C --

    # -- G --
    
    def get_targets(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.target_column_name, rtype)
    
    def get_upper_bounds(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.upper_bound_column_name, rtype)
    
    def get_lower_bounds(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.lower_bound_column_name, rtype)
    
    def get_confidence_scores(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.confidence_score_column_name, rtype)
    
    # -- I --

    @classmethod
    def import_from_path(cls, *args, 
                target_column_name:str=None, 
                upper_bound_column_name:str=None, 
                lower_bound_column_name:str=None, 
                confidence_score_column_name:str=None, 
                **kwargs) -> 'FluxTable':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param target_column_name: The name of the target column
        :type target_column_name: `str`
        :param upper_bound_column_name: The name of the upper-bound column
        :type upper_bound_column_name: `str`
        :param lower_bound_column_name: The name of the lower-bound column
        :type lower_bound_column_name: `str`
        :param confidence_score_column_name: The name of the confidence-score column
        :type confidence_score_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed csv table
        :rtype: FluxTable
        """
        
        csv_table = super().import_from_path(*args, index_col=0, **kwargs)
        target_column_name = target_column_name or cls.DEFAULT_TARGET_COLUMN_NAME
        upper_bound_column_name = upper_bound_column_name or cls.DEFAULT_UPPER_BOUND_COLUMN_NAME
        lower_bound_column_name = lower_bound_column_name or cls.DEFAULT_LOWER_BOUND_COLUMN_NAME
        confidence_score_column_name = confidence_score_column_name or cls.DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME

        if not csv_table.column_exists( target_column_name ):
            raise BadRequestException(f"Cannot import FluxTable. No target found (no column with name '{target_column_name}')")
            
        if not csv_table.column_exists( upper_bound_column_name ):
            raise BadRequestException(f"Cannot import FluxTable. No upper bound found (no column with name '{upper_bound_column_name}')")
            
        if not csv_table.column_exists( lower_bound_column_name ):
            raise BadRequestException(f"Cannot import FluxTable. No lower bound found (no column with name '{lower_bound_column_name}')")
            
        if not csv_table.column_exists( confidence_score_column_name ):
            raise BadRequestException(f"Cannot import FluxTable. No confidence score found (no column with name '{confidence_score_column_name}')")
        
        csv_table.target_column_name = target_column_name
        csv_table.upper_bound_column_name = upper_bound_column_name
        csv_table.lower_bound_column_name = lower_bound_column_name
        csv_table.confidence_score_column_name = confidence_score_column_name
        return csv_table

# ####################################################################
#
# Importer class
#
# ####################################################################
    
@task_decorator("FluxImporter")
class FluxImporter(TableImporter):
    input_specs = {'file' : File}
    output_specs = {'data': FluxTable}
    config_specs = {
        **TableImporter.config_specs,
        'target_column_name': StrParam(default_value=FluxTable.DEFAULT_TARGET_COLUMN_NAME, description="The name of the target column"),
        'lower_bound_column_name': StrParam(default_value=FluxTable.DEFAULT_LOWER_BOUND_COLUMN_NAME, description="The name of the lower-bound column"),
        'upper_bound_column_name': StrParam(default_value=FluxTable.DEFAULT_UPPER_BOUND_COLUMN_NAME, description="The name of the upper-bound column"),
        'confidence_score_column_name': StrParam(default_value=FluxTable.DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME, description="The name of the upper-bound column"),
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

@task_decorator("FluxExporter")
class FluxExporter(TableExporter):
    input_specs = {'data': FluxTable}
    output_specs = {'file' : File}
    config_specs = {
        **TableExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

@task_decorator("FluxLoader")
class FluxLoader(TableLoader):
    input_specs = {}
    output_specs = {'data' : FluxTable}
    config_specs = {
        **TableLoader.config_specs,
        'target_column_name': StrParam(default_value=FluxTable.DEFAULT_TARGET_COLUMN_NAME, description="The name of the target column"),
        'lower_bound_column_name': StrParam(default_value=FluxTable.DEFAULT_LOWER_BOUND_COLUMN_NAME, description="The name of the lower-bound column"),
        'upper_bound_column_name': StrParam(default_value=FluxTable.DEFAULT_UPPER_BOUND_COLUMN_NAME, description="The name of the upper-bound column"),
        'confidence_score_column_name': StrParam(default_value=FluxTable.DEFAULT_CONFIDENCE_SCORE_COLUMN_NAME, description="The name of the upper-bound column"),
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

@task_decorator("FluxDumper")
class FluxDumper(TableDumper):
    input_specs = {'data' : FluxTable}
    output_specs = {}
    config_specs = {
        **TableDumper.config_specs,
    }