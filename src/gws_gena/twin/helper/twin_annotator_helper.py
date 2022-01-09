# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BadRequestException, Task

from ...fba.fba_result import FBAResult
from ..flat_twin import FlatTwin
from ..twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


class TwinAnnotatorHelper():

    @staticmethod
    def annotate(twin: Twin, fba_result: FBAResult):
        if isinstance(twin, FlatTwin):
            raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")

        flat_twin: FlatTwin = twin.flatten()
        flux_rev_mapping = flat_twin.reverse_mapping
        annotated_twin = Twin()
        for k in twin.networks:
            net = twin.networks[k]
            ctx = twin.network_contexts[net.uid]
            net = net.copy()
            for rnx_id in net.reactions:
                rxn = net.reactions[rnx_id]
                net_name = net.name
                flat_rxn_id = flux_rev_mapping[net_name][rnx_id]
                fluxes = fba_result.get_fluxes_by_reaction_ids( [flat_rxn_id] )
                rxn.set_estimate({
                    "value": fluxes.loc[:, "value"],
                    "lower_bound": fluxes.loc[:, "lower_bound"],
                    "upper_bound": fluxes.loc[:, "upper_bound"],
                })
            annotated_twin.add_network(net, related_context=ctx.copy())
        return annotated_twin
