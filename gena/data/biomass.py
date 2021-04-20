# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import List

from gws.logger import Error
from gws.model import Process, ResourceSet
from gws.file import File
from gws.csv import CSVData, Loader, Dumper, Importer, Exporter

# ####################################################################
#
# Biomass Datatable class
#
# ####################################################################

class BiomassData(CSVData): 
    
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
    def _import(cls, *args, chebi_column_name:str="chebi_id", biomass_column_name:str="biomass", **kwargs) -> 'BiomassData':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param biomass_column_name: The name of the column containing the biomass equation
        :type biomass_column_name: `str`
        :param kwargs: Additional parameters passed to the superclass
        :type kwargs: `dict`
        :returns: the parsed data
        :rtype BiomassData
        """
        
        data = super()._import(*args, index_col=0, **kwargs)
        if not data.column_exists( chebi_column_name ):
            raise Error("BiomassData", "task", f"No CheBI ID column found (no column with name '{chebi_column_name}')")
        
        if not data.column_exists( biomass_column_name ):
            raise Error("BiomassData", "task", f"No biomass equation found (no column with name '{biomass_column_name}')")
        
        data.biomass_column_name = biomass_column_name
        data.chebi_column_name = chebi_column_name
        return data
    
# ####################################################################
#
# Importer class
#
# ####################################################################
    
class BiomassImporter(Importer):
    input_specs = {'file' : File}
    output_specs = {'data': BiomassData}
    config_specs = {
        **Importer.config_specs,
        'chebi_column_name': {"type": 'str', "default": 'chebi_id', "description": "The CheBI ID column name"},
        'biomass_column_name': {"type": 'str', "default": 'biomass', "description": "The biomass equation column name"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class BiomassExporter(Exporter):
    input_specs = {'data': BiomassData}
    output_specs = {'file' : File}
    config_specs = {
        **Exporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class BiomassLoader(Loader):
    input_specs = {}
    output_specs = {'data' : BiomassData}
    config_specs = {
        **Loader.config_specs,
        'chebi_column_name': {"type": 'str', "default": 'chebi_id', "description": "The CheBI ID column name"},
        'biomass_column_name': {"type": 'str', "default": 'biomass', "description": "The biomass equation column name"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class BiomassDumper(Dumper):
    input_specs = {'data' : BiomassData}
    output_specs = {}
    config_specs = {
        **Dumper.config_specs,
    }