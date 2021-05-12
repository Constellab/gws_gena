# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import pandas as pd

from gws.json import JSONData
from gws.typing import Path
from gws.shell import Shell
from gws.file import File
from gws.settings import Settings
from gws.logger import Error

from gena.fba import FluxAnalyzer, FluxAnalyzerResult
from gena.biomodel import Biomodel
from gena.network import Network
from gena.context import Context

class FluxCheckerResult(FluxAnalyzerResult):
    pass

class FluxChecker(FluxAnalyzer):
    
    input_specs = { 'biomodel': (Biomodel,) }
    output_specs = { 'file': (FluxCheckerResult,) }
    #config_specs = {
    #    "eq_tol": {"type": float, "default": 1e-6, "Description": "Equality constraint tolerance"},
    #    "ineq_tol": {"type": float, "default": 1e-6, "Description": "Inequality constraint tolerance"},
    #    "least_energy_weight": {"type": float, "default": 0.001, "min": 0, "max": 1, "Description": "The least energy weight. The higher it is, lower will be sum of fluxes"},
    #    "use_random_starting_point": {"type": bool, "default": True, "Description": "True to use random initial conditions to explore to flux space, False otherwise. If number_of_randomizations > 1, then this parameter will operate to True."},
    #    "number_of_randomizations": {"type": int, "default": 5, "Description": "Number of random initial conditions to use to explore the flux space."}
    #}
    
    # -- B --
    
    def build_command(self) -> list:
        settings = Settings.retrieve()
        _dir = settings.get_dependency_dir("gena")
        bin_file = os.path.join(_dir, "bin/fba/fba")
        
        biomodel = self.input["biomodel"]
        flat_bio = biomodel.flatten()

        # remove cofactors
        # flat_bio = flat_bio.remove_cofactors()
        
        self.network_file = os.path.join(self.cwd.name,"network.json")
        with open(self.network_file, "w") as fp:
            json.dump(flat_bio["network"], fp) 
        
        self.context_file = os.path.join(self.cwd.name,"context.json")
        with open(self.context_file, "w") as fp:
            #json.dump(flat_bio["context"], fp)
            json.dump({"measures": []}, fp)
                
        # override config
        #nrnd = min(5000, 10 * biomodel.number_of_reactions)
        self.set_param("least_energy_weight", 1e-6)
        self.set_param("use_random_starting_point", True)
        #self.set_param("number_of_randomizations", nrnd)
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
    
        
class BiomodelBuilder(Shell):
    input_specs = { 'network': (Network,), 'context': (Context,)  }
    output_specs = { 'biomodel': (Biomodel,) }
    config_specs = {}
    
    async def task(self):
        net = self.input["network"]
        ctx = self.input["context"]
        
        bio = Biomodel()
        bio.add_network(net)
        bio.add_context(ctx, related_network=net)
        bio.save()
        
        self.output["biomodel"] = bio
        

class PhenoChecker(FluxAnalyzer):
    pass