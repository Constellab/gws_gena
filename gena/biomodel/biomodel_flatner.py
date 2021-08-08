# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.process import Process
from .biomodel import BioModel, FlatBioModel

class BioModelFlattener(Process):
    input_specs = { 'biomodel': (BioModel,), }
    output_specs = { 'flat_biomodel': (FlatBioModel,) }
    config_specs = {}
    
    async def task(self):
        bio = self.input["biomodel"]
        flat_json: dict = bio.flatten()
        self.output["flat_biomodel"] = FlatBioModel(flat_json)