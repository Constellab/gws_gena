# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.json import JSONDAta
from gws.typing import Path
from gws.shell import EasyShell

 


from gena.twin import Twin, Phenotype

class FbaResult(JSONDAta):
    pass

class Fba(EasyShell):
    
    input_specs = {'model': (Twin,) }
    output_specs = {'result': (FbaResult,) }
    config_specs = {}
    
    def build_command(self) -> list:
        settings = Settings.retrieve()
        _dir = settings.get_extern_dirs("gena-cpp")
        
        bin_dir = os.path.join(_dir,"bazel-bin","")
        
