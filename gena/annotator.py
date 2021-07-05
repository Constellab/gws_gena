# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math

from gws.model import Process
from .biomodel import BioModel


from .base_fba import AbstractFBAResult
from .fast_fba import FastFBAResult

# ####################################################################
#
# BioModelAnnotator class
#
# ####################################################################

class BioModelAnnotator(Process):
    input_specs = { 'biomodel': (BioModel,), 'fba_result': (AbstractFBAResult,) }
    output_specs = { 'biomodel': (BioModel,) }

    async def task(self):
        input_biomodel = self.input["biomodel"]
        flat_bio = input_biomodel.flatten()
        flux_rev_mapping = flat_bio["reverse_mapping"]
        fba_result = self.input["fba_result"]

        annotated_bio = BioModel()
        for k in input_biomodel.networks:
            net = input_biomodel.networks[k].copy()

            for rnx_id in net.reactions:
                rxn = net.reactions[rnx_id]
                net_name = net.name
                flat_id = flux_rev_mapping[net_name][rnx_id]
                fluxes = fba_result.render__fluxes__as_table()
                rxn.set_estimate({
                    "value": fluxes.loc[flat_id, "value"],
                    "lower_bound": fluxes.loc[flat_id, "lower_bound"],
                    "upper_bound": fluxes.loc[flat_id, "upper_bound"],
                })

            net.save()
            annotated_bio.add_network(net)

        self.output["biomodel"] = annotated_bio