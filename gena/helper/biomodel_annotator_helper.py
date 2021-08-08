# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import math

from gws.process import Process
from gws.exception.bad_request_exception import BadRequestException

from ..biomodel.biomodel import BioModel, FlatBioModel
from ..fba.fba_result import FBAResult

# ####################################################################
#
# BioModelAnnotator class
#
# ####################################################################

class BioModelAnnotatorHelper():

    @staticmethod
    def annotate(biomodel: BioModel, fba_result: FBAResult):
        if isinstance(biomodel, FlatBioModel):
            raise BadRequestException("Cannot annotate de FlabBioModel. A non-flat BioModel is required")

        flat_dict: dict = biomodel.flatten()
        flux_rev_mapping = flat_dict["reverse_mapping"]
        annotated_bio = BioModel()
        for k in biomodel.networks:
            net = biomodel.networks[k]
            ctx = biomodel.network_contexts[net.uri]
            net = net.copy()
            for rnx_id in net.reactions:
                rxn = net.reactions[rnx_id]
                net_name = net.name
                flat_rxn_id = flux_rev_mapping[net_name][rnx_id]
                fluxes = fba_result.render__fluxes__as_table()
                rxn.set_estimate({
                    "value": fluxes.loc[flat_rxn_id, "value"],
                    "lower_bound": fluxes.loc[flat_rxn_id, "lower_bound"],
                    "upper_bound": fluxes.loc[flat_rxn_id, "upper_bound"],
                })
            annotated_bio.add_network(net, related_context=ctx.copy())
        return annotated_bio