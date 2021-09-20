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

from gws_core import (Resource, Path, Shell, File, Settings, 
                        task_decorator, FloatParam, StrParam, BoolParam, IntParam,
                        ConfigParams, TaskInputs, TaskOutputs, Utils)
from ..twin.twin import Twin, FlatTwin
from ..twin.twin_context import TwinContext
from ..network.network import Network
from .deprec_fba_result import DeprecFBAResult

@task_decorator("DeprecFBA")
class DeprecFBA(Shell):
    input_specs = { 'twin': (Twin,) }
    output_specs = { 'result': (DeprecFBAResult,) }
    config_specs = {
        "eq_tol": FloatParam(default_value=1e-6, description="Equality constraint tolerance"),
        "ineq_tol": FloatParam(default_value=1e-6, description="Inequality constraint tolerance"),
        "algorithm": StrParam(default_value="bfgs", allowed_values=["bfgs", "lbfgs"], description="Type of optimization algorithm"),
        "use_hard_bounds": BoolParam(default_value=True, description="True to use hard bounds, Flase otherwise."),
        "verbose": BoolParam(default_value=False, description="True to verbose, Flase otherwise."),
        "least_energy_weight": FloatParam(default_value=0.0, min_value=0, max_value=1, description="The least energy weight. The higher it is, lower will be sum of fluxes"),
        "use_random_starting_point": BoolParam(default_value=True, description="True to use random initial conditions to explore to flux space, False otherwise. If number_of_randomizations > 1, then this parameter will operate to True."),
        "number_of_randomizations": IntParam(default_value=100, description="Number of random initial conditions to use to explore the flux space.")
    }
    
    # -- A --
      
    # -- B --
    
    #def build_command(self) -> list:
    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        brick_dir = Utils.get_brick_path(self)
        bin_file = os.path.join(brick_dir, "bin/fba/fba")
        twin = inputs["twin"]
        self.__flat_bio: dict = twin.flatten()
        network_file = os.path.join(self.cwd.name,"network.json")
        with open(network_file, "w") as fp:
            json.dump(self.__flat_bio["twin"]["networks"][0], fp) 
        
        context_file = os.path.join(self.cwd.name,"context.json")
        with open(context_file, "w") as fp:
            json.dump(self.__flat_bio["twin"]["contexts"][0], fp)
        
        config_file = os.path.join(self.cwd.name,"config.json")
        with open(config_file, "w") as fp:
            json.dump(params, fp)
 
        cmd = [ 
            bin_file, 
            "--run", "fba",
            "--network", network_file,
            "--context", context_file,
            "--config", config_file,
            "--out", self._build_output_file_path()
        ]
        return cmd
    
    def _build_output_file_path(self):
        return os.path.join(self.cwd.name,"result.json")


    # -- C --
    
    def compute_progress_bar_value(self, stdout_count: int=0, stdout_line: str="") -> tuple:
        value = stdout_count / self.get_param("number_of_randomizations")
        message = stdout_line
        if value and value < 100:
            # prevent blocking the progress bar if the current is not well computed by the user
            self.update_progress_value(value, message=message)
            
    # -- G --
    
    #def gather_outputs(self, stdout: str=None):
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        bio = inputs["twin"]   
        file = DeprecFBAResult(twin=bio)
        file.path = self._build_output_file_path()
        return {"result": file}

    # -- T --
