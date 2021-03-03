# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import List

from gws.logger import Error
from gws.model import Process, ResourceSet
from gws.file import File
from gws.csv import CSVData, \
                    Loader as CSVLoader, Dumper as CSVDumper, \
                    Importer as CSVImporter, Exporter as CSVExporter

from biota.enzyme import Enzyme
from biota.taxonomy import Taxonomy
from biota.enzyme import Enzyme

# ####################################################################
#
# EC Number Datatable class
#
# ####################################################################

class ECData(CSVData):
    
    EC_COLUMN_NAME = "ec_number"
    
    # -- E --
    
    @property
    def ec_column_name(self):
        return self.data.get('ec_column_name', self.EC_COLUMN_NAME)

    @ec_column_name.setter
    def ec_column_name(self, name):
        self.data['ec_column_name'] = name
    
    # -- F --
    
    def get_ec_numbers(self, rtype='list') -> ('DataFrame', list):
        if rtype == 'list':
            return list(self.table[self.ec_column_name].values)
        else:
            return self.table[[self.ec_column_name]]
    
    # -- I --

    @classmethod
    def _import(cls, *args, ec_column_name:str="ec_number", **kwargs) -> 'ECData':
        """ 
        Import from a repository
        
        Additional parameters
        
        :param ec_column_name: The name of the column containing the EC numbers
        :type ec_column_name: `str`
        :returns: the parsed data
        :rtype ECData
        """
        
        data = super()._import(*args, **kwargs)
        if not data.column_exists( ec_column_name ):
            raise Error("ECData", "task", f"No ec numbers found (no column with name 'ec_column_name')")
        
        data.ec_column_name = ec_column_name
        return data
    
# ####################################################################
#
# Importer class
#
# ####################################################################
    
class Importer(CSVImporter):
    input_specs = {'file' : File}
    output_specs = {'resource': ECData}
    config_specs = {
        **CSVImporter.config_specs,
        'ec_column_name': {"type": 'str', "default": 'ec_number', "description": "The name of the EC Number column name"},
    }

# ####################################################################
#
# Exporter class
#
# ####################################################################

class Exporter(CSVExporter):
    input_specs = {'resource': ECData}
    output_specs = {'file' : File}
    config_specs = {
        **CSVExporter.config_specs,
    }

# ####################################################################
#
# Loader class
#
# ####################################################################

class Loader(CSVLoader):
    input_specs = {}
    output_specs = {'resource' : CSVData}
    config_specs = {
        **CSVLoader.config_specs,
        'ec_column_name': {"type": 'str', "default": 'ec_number', "description": "The name of the EC Number column name"},
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################

class Dumper(CSVDumper):
    input_specs = {'resource' : CSVData}
    output_specs = {}
    config_specs = {
        **CSVDumper.config_specs,
    }