# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import List

from gws.file import File
from gws.csv import CSVData, CSVLoader, CSVDumper, CSVImporter, CSVExporter
from gws.exception.bad_request_exception import BadRequestException

# ####################################################################
#
# Flux Datatable class
#
# ####################################################################

class FluxData(CSVData):
    """ 
    Represents experimentally-measured (or user-defined) flux data
        
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
    
    TARGET_COLUMN_NAME = "target"
    UPPER_BOUND_COLUMN_NAME = "upper_bound"
    LOWER_BOUND_COLUMN_NAME = "lower_bound"
    CONFIDENCE_SCORE_COLUMN_NAME = "confidence_score"
        
    # -- C --
    
    @property
    def confidence_score_column_name(self):
        return self.data.get('confidence_score_column_name', self.CONFIDENCE_SCORE_COLUMN_NAME)

    @confidence_score_column_name.setter
    def confidence_score_column_name(self, name):
        self.data['confidence_score_column_name'] = name
    
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
    def _import(cls, *args, 
                target_column_name:str="target", 
                upper_bound_column_name:str="upper_bound", 
                lower_bound_column_name:str="lower_bound", 
                confidence_score_column_name:str="confidence_score", 
                **kwargs) -> 'FluxData':
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
        :returns: the parsed data
        :rtype: FluxData
        """
        
        data = super()._import(*args, index_col=0, **kwargs)

        if not data.column_exists( target_column_name ):
            raise BadRequestException(f"Cannot import FluxData. No target found (no column with name '{target_column_name}')")
            
        if not data.column_exists( upper_bound_column_name ):
            raise BadRequestException(f"Cannot import FluxData. No upper bound found (no column with name '{upper_bound_column_name}')")
            
        if not data.column_exists( lower_bound_column_name ):
            raise BadRequestException(f"Cannot import FluxData. No lower bound found (no column with name '{lower_bound_column_name}')")
            
        if not data.column_exists( confidence_score_column_name ):
            raise BadRequestException(f"Cannot import FluxData. No confidence score found (no column with name '{confidence_score_column_name}')")
        
        data.target_column_name = target_column_name
        data.upper_bound_column_name = upper_bound_column_name
        data.lower_bound_column_name = lower_bound_column_name
        data.confidence_score_column_name = confidence_score_column_name
        return data
    
    # -- L --
    
    @property
    def lower_bound_column_name(self):
        return self.data.get('lower_bound_column_name', self.LOWER_BOUND_COLUMN_NAME)

    @lower_bound_column_name.setter
    def lower_bound_column_name(self, name):
        self.data['lower_bound_column_name'] = name
    
    # -- T --
    
    @property
    def target_column_name(self):
        return self.data.get('target_column_name', self.TARGET_COLUMN_NAME)

    @target_column_name.setter
    def target_column_name(self, name):
        self.data['target_column_name'] = name
        
    # -- U --
    
    @property
    def upper_bound_column_name(self):
        return self.data.get('upper_bound_column_name', self.UPPER_BOUND_COLUMN_NAME)

    @upper_bound_column_name.setter
    def upper_bound_column_name(self, name):
        self.data['upper_bound_column_name'] = name
        
# ####################################################################
#
# Importer class
#
# ####################################################################
    
class FluxImporter(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {'data': FluxData}
    config_specs = {
        **CSVImporter.config_specs,
        'target_column_name': {"type": 'str', "default": FluxData.TARGET_COLUMN_NAME, "description": "The name of the target column"},
        'lower_bound_column_name': {"type": 'str', "default": FluxData.LOWER_BOUND_COLUMN_NAME, "description": "The name of the lower-bound column"},
        'upper_bound_column_name': {"type": 'str', "default": FluxData.UPPER_BOUND_COLUMN_NAME, "description": "The name of the upper-bound column"},
        'confidence_score_column_name': {"type": 'str', "default": FluxData.CONFIDENCE_SCORE_COLUMN_NAME, "description": "The name of the upper-bound column"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class FluxExporter(CSVExporter):
    input_specs = {'data': FluxData}
    output_specs = {'file' : File}
    config_specs = {
        **CSVExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class FluxLoader(CSVLoader):
    input_specs = {}
    output_specs = {'data' : FluxData}
    config_specs = {
        **CSVLoader.config_specs,
        'target_column_name': {"type": 'str', "default": FluxData.TARGET_COLUMN_NAME, "description": "The name of the target column"},
        'lower_bound_column_name': {"type": 'str', "default": FluxData.LOWER_BOUND_COLUMN_NAME, "description": "The name of the lower-bound column"},
        'upper_bound_column_name': {"type": 'str', "default": FluxData.UPPER_BOUND_COLUMN_NAME, "description": "The name of the upper-bound column"},
        'confidence_score_column_name': {"type": 'str', "default": FluxData.CONFIDENCE_SCORE_COLUMN_NAME, "description": "The name of the upper-bound column"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class FluxDumper(CSVDumper):
    input_specs = {'data' : FluxData}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }