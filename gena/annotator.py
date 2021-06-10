# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math

from gws.model import Process
from .fba import BioModel
from .fba import FluxAnalyzerResult

# ####################################################################
#
# BioModelAnnotator class
#
# ####################################################################

class BioModelAnnotator(Process):
    input_specs = { 'biomodel': (BioModel,), 'flux_analyzer_result': (FluxAnalyzerResult,) }
    output_specs = { 'biomodel': (BioModel,) }

    async def task(self):
        input_biomodel = self.input["biomodel"]
        flat_bio = input_biomodel.flatten()
        flux_rev_mapping = flat_bio["reverse_mapping"]
        flux_analyzer_result = self.input["flux_analyzer_result"]

        print(flux_rev_mapping)

        annotated_bio = BioModel()
        for k in input_biomodel.networks:
            net = input_biomodel.networks[k].copy()

            for rnx_id in net.reactions:
                rxn = net.reactions[rnx_id]
                net_name = net.name
                
                fluxes = flux_analyzer_result.render__flux_ranges__as_table()
                flat_id = flux_rev_mapping[net_name][rnx_id]

                val = fluxes.loc[flat_id, "mean"]
                std = fluxes.loc[flat_id, "std"]
                rxn.set_estimate({
                    "value": val,
                    "lower_bound": (val if math.isnan(std) else val-std),
                    "upper_bound": (val if math.isnan(std) else val+std)
                })

            net.save()
            annotated_bio.add_network(net)

        self.output["biomodel"] = annotated_bio