# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import pandas as pd
from pandas import DataFrame
import pandas as pd
from scipy import stats

from gws.resource import Resource
from gws.typing import Path
from gws.shell import Shell
from gws.file import File
from gws.settings import Settings
from ...biomodel.biomodel import BioModel, FlatBioModel
from ...biomodel.context import Context
from ...network.network import Network
from .fba_result import FBAResult

class FBA(Shell):
    input_specs = { 'biomodel': (BioModel,) }
    output_specs = { 'result': (FBAResult,) }
    config_specs = {
        "eq_tol": {"type": float, "default": 1e-6, "Description": "Equality constraint tolerance"},
        "ineq_tol": {"type": float, "default": 1e-6, "Description": "Inequality constraint tolerance"},
        "algorithm": {"type": str, "default": "bfgs", "allow_values": ["bfgs", "lbfgs"], "Description": "Type of optimization algorithm"},
        "use_hard_bounds": {"type": bool, "default": True, "Description": "True to use hard bounds, Flase otherwise."},
        "verbose": {"type": bool, "default": False, "Description": "True to verbose, Flase otherwise."},
        "least_energy_weight": {"type": float, "default": 0.0, "min": 0, "max": 1, "Description": "The least energy weight. The higher it is, lower will be sum of fluxes"},
        "use_random_starting_point": {"type": bool, "default": True, "Description": "True to use random initial conditions to explore to flux space, False otherwise. If number_of_randomizations > 1, then this parameter will operate to True."},
        "number_of_randomizations": {"type": int, "default": 100, "Description": "Number of random initial conditions to use to explore the flux space."}
    }
    
    # -- A --
      
    # -- B --
    
    def build_command(self) -> list:
        settings = Settings.retrieve()
        _dir = settings.get_dependency_dir("gena")
        bin_file = os.path.join(_dir, "bin/fba/fba")
        biomodel = self.input["biomodel"]
        self.__flat_bio: dict = biomodel.flatten()
        self.network_file = os.path.join(self.cwd.name,"network.json")
        with open(self.network_file, "w") as fp:
            json.dump(self.__flat_bio["biomodel"]["networks"][0], fp) 
        
        self.context_file = os.path.join(self.cwd.name,"context.json")
        with open(self.context_file, "w") as fp:
            json.dump(self.__flat_bio["biomodel"]["contexts"][0], fp)
        
        self.config_file = os.path.join(self.cwd.name,"config.json")
        with open(self.config_file, "w") as fp:
            json.dump(self.config.params, fp)
 
        self.output_file = os.path.join(self.cwd.name,"result.json")
        cmd = [ 
            bin_file, 
            "--run", "fba",
            "--network", self.network_file,
            "--context", self.context_file,
            "--config", self.config_file,
            "--out", self.output_file
        ]
        return cmd
    
    # -- C --
    
    def compute_progress_bar_value(self, stdout_count: int=0, stdout_line: str="") -> tuple:
        value = stdout_count / self.get_param("number_of_randomizations")
        message = stdout_line
        if value and value < self.progress_bar.get_max_value():
            # prevent blocking the progress bar if the current is not well computed by the user
            self.progress_bar.set_value(value, message=message)
            
    # -- G --
    
    def gather_outputs(self, stdout: str=None):
        t = self.out_port("result").get_default_resource_type()     
        bio = self.input["biomodel"]   
        file = t(biomodel=bio)
        file.path = self.output_file
        self.output["result"] = file
        self.data["stdout"] = stdout

    # -- T --
