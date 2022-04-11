# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BadRequestException, Table, Task

from ..flat_twin import FlatTwin
from ..twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


class TwinAnnotatorHelper():

    @staticmethod
    def annotate(twin: Twin, fba_result: 'FBAResult'):
        if isinstance(twin, FlatTwin):
            raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")

        flat_twin: FlatTwin = twin.flatten()
        flux_rev_mapping = flat_twin.reverse_mapping
        annotated_twin = Twin()
        for net in twin.networks.values():
            ctx_name = twin.network_contexts[net.name]
            ctx = twin.contexts[ctx_name]
            for rnx_id in net.reactions:
                rxn = net.reactions[rnx_id]
                net_name = net.name
                flat_rxn_id = flux_rev_mapping[net_name][rnx_id]
                fluxes = fba_result.get_fluxes_by_reaction_ids([flat_rxn_id])
                rxn.set_estimate({
                    "value": fluxes.at[flat_rxn_id, "value"],
                    "lower_bound": fluxes.at[flat_rxn_id, "lower_bound"],
                    "upper_bound": fluxes.at[flat_rxn_id, "upper_bound"],
                })
            annotated_twin.add_network(net, related_context=ctx)
        return annotated_twin

        # if isinstance(twin, FlatTwin):
        #     raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")
        # flat_twin: FlatTwin = twin.flatten()
        # flux_rev_mapping = flat_twin.reverse_mapping
        # flux_data = fba_result.get_flux_table().get_data()
        # for net in twin.networks.values():
        #     for rnx_id in net.reactions:
        #         rxn = net.reactions[rnx_id]
        #         net_name = net.name
        #         flat_rxn_id = flux_rev_mapping[net_name][rnx_id]
        #         rxn.set_estimate({
        #             "value": flux_data.at[flat_rxn_id, "value"],
        #             "lower_bound": flux_data.at[flat_rxn_id, "lower_bound"],
        #             "upper_bound": flux_data.at[flat_rxn_id, "upper_bound"],
        #         })
