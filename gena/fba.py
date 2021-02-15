# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os

from gws.json import JSONData
from gws.typing import Path
from gws.shell import Shell
from gws.file import File
from gws.settings import Settings
from gws.logger import Error

from gena.biomodel import Biomodel

class FBAResult(JSONData):
    pass

class FluxAnalyzer(Shell):
    
    input_specs = { 'biomodel': (Biomodel,) }
    output_specs = { 'file': (File,) }
    config_specs = {
        "eq_tol": {"type": float, "default": 1e-6, "Description": "Equality constraint tolerance"},
        "ineq_tol": {"type": float, "default": 1e-6, "Description": "Inequality constraint tolerance"},
        "least_energy_weight": {"type": float, "default": 0.001, "min": 0, "max": 1, "Description": "The least energy weight. The higher it is, lower will be sum of fluxes"},
        "use_random_starting_point": {"type": bool, "default": True, "Description": "True to use random initial conditions to explore to flux space, False otherwise. If number_of_randomizations > 1, then this parameter will operate to True."},
        "number_of_randomizations": {"type": int, "default": 5, "Description": "Number of random initial conditions to use to explore the flux space."}
    }
    
    def after_command(self, stdout: str=None):
        f = File()
        f.path = self.output_file
        self.output["file"] = f
        self.data["stdout"] = stdout
    
    def build_command(self) -> list:
        settings = Settings.retrieve()
        _dir = settings.get_dependency_dir("gena")
        bin_file = os.path.join(_dir, "bin/build/fba")
        
        biomodel = self.input["biomodel"]
        self.network_file = os.path.join(self.cwd.name,"network.json")
        self.context_file = os.path.join(self.cwd.name,"context.json")
        self.config_file = os.path.join(self.cwd.name,"config.json")
        self.output_file = os.path.join(self.cwd.name,"result.json")
        
        flat_bio = biomodel.flatten()

        with open(self.network_file, "w") as fp:
            json.dump(flat_bio["network"], fp)
        
        with open(self.context_file, "w") as fp:
            json.dump(flat_bio["context"], fp)
            
        with open(self.config_file, "w") as fp:
            json.dump(self.config.params, fp)
            
        cmd = [ 
            bin_file, 
            "--run", "fba",
            "--network", self.network_file,
            "--context", self.context_file,
            "--config", self.config_file,
            "--out", self.output_file
        ]
        
        return cmd