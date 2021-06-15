# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import pandas as pd
from pandas import DataFrame

from gws.json import JSONData
from gws.typing import Path
from gws.shell import Shell
from gws.file import File
from gws.settings import Settings
from gws.logger import Error

from .biomodel import BioModel
from .network import Network
from .context import Context

from scipy import stats

class FluxAnalyzerResult(File):
    _content = None
    _default_zero_flux_threshold = 0.01

    @property
    def content(self)->dict:
        if not self._content:
            self._content = json.loads(self.read())
        
        return self._content
    
    def compute_zero_flux_threshold(self) -> float:
        df = self.render__sv_ranges__as_table()
        m = df["mean"]
        try:
            _,p = stats.normaltest(m)
            if p < 0.05:
                return 2.0 * m.std()
            else:
                return self._default_zero_flux_threshold
        except:
            return self._default_zero_flux_threshold

    # -- K --
    
    @property
    def ker_of_identif(self)->dict:
        return self.content["problem"]["ker_of_identif"]
    
    @property
    def ker_of_intern_stoich(self)->dict:
        return self.content["problem"]["ker_of_intern_stoich"]
    
    # -- P --
    
    @property
    def problem(self)->dict:
        return self.content["problem"]
    
    # -- R --
    
    @property
    def rank_of_identif(self)->dict:
        return self.content["problem"]["rank_of_identif"]
    
    @property
    def rank_of_intern_stoich(self)->dict:
        return self.content["problem"]["rank_of_intern_stoich"]
    
    # -- S --
    
    @property
    def stoich_matrix(self)->dict:
        return self.content["problem"]["S"]
    
    @property
    def sv(self)->dict:
        return self.content["problem"]["sv"]
    
    @property
    def solutions(self)->dict:
        return self.content["problem"]["solutions"]
    
    @property
    def solver_success(self)->dict:
        return self.content["problem"]["solver_success"]
    
    # -- V --
    
    def render__sv_distrib__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = DataFrame(
            self.sv["data"], 
            index=self.sv["row_names"], 
            columns=self.sv["col_names"]
        )
        
        if only_sucess:
            success = self.render__solver_success__as_table()
            success_columns = df.columns[success.iloc[0,:]]
            df = df[ success_columns ]
            
        return df
    
    def render__sv_ranges__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = self.render__sv_distrib__as_table(only_sucess=only_sucess)

        Q1 = df.quantile(q=0.25, axis=1)
        Q2 = df.quantile(q=0.5, axis=1)
        Q3 = df.quantile(q=0.75, axis=1)
        df = pd.concat( 
            [ 
                df.mean(axis=1), 
                df.std(axis=1), 
                df.min(axis=1), 
                df.max(axis=1),
                Q2, Q3 - Q1, Q1, Q3
            ],
            axis=1 
        )
        df.columns = [ "mean", "std", "min", "max", "Q2", "IQR", "Q1", "Q3" ]
        df = df.sort_values(by=["std"])
        return df
    
    def render__ker_of_identif__as_table(self) -> DataFrame:
        df = DataFrame(
            self.ker_of_identif["data"], 
            index=self.ker_of_identif["row_names"], 
            columns=self.ker_of_identif["col_names"]
        )
        return df
    
    def render__ker_of_intern_stoich__as_table(self) -> DataFrame:
        df = DataFrame(
            self.ker_of_intern_stoich["data"], 
            index=self.ker_of_intern_stoich["row_names"], 
            columns=self.ker_of_intern_stoich["col_names"]
        )
        return df
    
    def render__solver_success__as_table(self) -> DataFrame:
        df = DataFrame(
            self.solver_success["data"], 
            index=self.solver_success["row_names"], 
            columns=self.solver_success["col_names"]
        )
        return df == 1.0
    
    def render__stoich_matrix__as_table(self) -> DataFrame:
        df = DataFrame(
            self.stoich_matrix["data"], 
            index=self.stoich_matrix["row_names"], 
            columns=self.stoich_matrix["col_names"]
        )
        return df
    
    def render__flux_ranges__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = self.render__flux_distrib__as_table(only_sucess=only_sucess)
        
        Q1 = df.quantile(q=0.25, axis=1)
        Q2 = df.quantile(q=0.5, axis=1)
        Q3 = df.quantile(q=0.75, axis=1)
        df = pd.concat( 
            [ 
                df.mean(axis=1), 
                df.std(axis=1), 
                df.min(axis=1), 
                df.max(axis=1),
                Q2, Q3 - Q1, Q1, Q3
            ],
            axis=1 
        )
        df.columns = [ "mean", "std", "min", "max", "Q2", "IQR", "Q1", "Q3" ]
        df = df.sort_values(by=["std"])
        return df
    
    def render__flux_distrib__as_table(self, only_sucess: bool = True) -> DataFrame:
        df = DataFrame(
            self.solutions["data"], 
            index=self.solutions["row_names"], 
            columns=self.solutions["col_names"]
        )
        
        if only_sucess:
            success = self.render__solver_success__as_table()
            success_columns = df.columns[success.iloc[0,:]]
            df = df[ success_columns ]
            
        return df
    
    # def render__feasible_fluxes__as_table(self, only_sucess: bool = True) -> DataFrame:
    #     df = self.render__sv_distrib__as_table(only_sucess=only_sucess)
    #     df = df.mean(axis=1)
    #     return df
    
class FluxAnalyzer(Shell):
    
    input_specs = { 'biomodel': (BioModel,) }
    output_specs = { 'file': (FluxAnalyzerResult,) }
    config_specs = {
        "eq_tol": {"type": float, "default": 1e-6, "Description": "Equality constraint tolerance"},
        "ineq_tol": {"type": float, "default": 1e-6, "Description": "Inequality constraint tolerance"},
        "algorithm": {"type": str, "default": "bfgs", "allow_values": ["bfgs", "lbfgs"], "Description": "Type of optimization algorithm"},
        "use_hard_bounds": {"type": bool, "default": True, "Description": "True to use hard bounds, Flase otherwise."},
        "verbose": {"type": bool, "default": False, "Description": "True to verbose, Flase otherwise."},
        "least_energy_weight": {"type": float, "default": 1e-6, "min": 0, "max": 1, "Description": "The least energy weight. The higher it is, lower will be sum of fluxes"},
        "use_random_starting_point": {"type": bool, "default": True, "Description": "True to use random initial conditions to explore to flux space, False otherwise. If number_of_randomizations > 1, then this parameter will operate to True."},
        "number_of_randomizations": {"type": int, "default": 100, "Description": "Number of random initial conditions to use to explore the flux space."}
    }
    
    # -- B --
    
    def build_command(self) -> list:
        settings = Settings.retrieve()
        _dir = settings.get_dependency_dir("gena")
        bin_file = os.path.join(_dir, "bin/fba/fba")
        
        biomodel = self.input["biomodel"]
        self.__flat_bio = biomodel.flatten()
        
        self.network_file = os.path.join(self.cwd.name,"network.json")
        with open(self.network_file, "w") as fp:
            json.dump(self.__flat_bio["network"], fp) 
        
        self.context_file = os.path.join(self.cwd.name,"context.json")
        with open(self.context_file, "w") as fp:
            json.dump(self.__flat_bio["context"], fp)
        
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
        t = self.out_port("file").get_default_resource_type()        
        file = t()
        file.path = self.output_file
        self.output["file"] = file
        self.data["stdout"] = stdout