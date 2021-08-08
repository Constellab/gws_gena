# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math

from gws.process import Process
from .biomodel import BioModel
from ..fba.fba_result import FBAResult
from ..helper.biomodel_annotator_helper import BioModelAnnotatorHelper

# ####################################################################
#
# BioModelAnnotator class
#
# ####################################################################

class BioModelAnnotator(Process):
    input_specs = { 'biomodel': (BioModel,), 'fba_result': (FBAResult,) }
    output_specs = { 'biomodel': (BioModel,) }

    async def task(self):
        biomodel = self.input["biomodel"]
        fba_result = self.input["fba_result"]
        annotated_bio: BioModel = BioModelAnnotatorHelper.annotate(biomodel, fba_result)
        self.output["biomodel"] = annotated_bio
