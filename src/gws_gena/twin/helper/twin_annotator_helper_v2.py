
from typing import List

from gws_gena.fba.fba_result import FBAResult
from gws_gena.helper.base_helper import BaseHelper
from gws_gena.twin.twin_v2 import TwinV2

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


class TwinAnnotatorHelperV2(BaseHelper):

    def annotate_from_fba_results(self, twin: TwinV2, fba_results: List[FBAResult]) -> TwinV2:
        """
        Annotate a twin using from FBAResult
        """

        network = twin.get_network()

        i = 0
        for fba_result in fba_results:
            fluxes = fba_result.get_fluxes_dataframe()
            name_network = network.network_dict["id"]
            if name_network is None :
                name_network = network.network_dict["name"]

            for reaction_id in network.get_reaction_ids():
                reaction_with_network_name = name_network + "_" + reaction_id

                flux_estimates = network.get_reaction_simulation_data(
                    reaction_id)

                flux_estimates[str(i)] = {
                    "value": fluxes.at[reaction_with_network_name, "value"],
                    "lower_bound": fluxes.at[reaction_with_network_name, "lower_bound"],
                    "upper_bound": fluxes.at[reaction_with_network_name, "upper_bound"],
                }

                network.set_reaction_simulation_data(
                    reaction_id, flux_estimates)

            i += 1

        return twin

    def annotate_from_fva_results(self, twin: TwinV2, fva_result: 'FVAResult'):
        """
        Annotate a twin using from FVAResult
        """

        return self.annotate_from_fba_results(twin, fva_result)

    def annotate_from_koa_result(self, twin: TwinV2, koa_result: 'KOAResult'):
        """
        Annotate a twin using from KOAResult
        """
        network = twin.get_network()
        simulations = koa_result.get_simulations()
        if len(simulations) == 0:
            raise Exception("At least one KO simulation is required")

        for condition in simulations:
            cond_id = condition["id"]

            fluxes = koa_result.get_flux_dataframe(cond_id)
            name_network = network.network_dict["id"]
            if name_network is None :
                name_network = network.network_dict["name"]
            for reaction_id in network.get_reaction_ids():
                reaction_with_network_name = name_network + "_" + reaction_id
                flux_estimates = network.get_reaction_simulation_data(reaction_id)
                #TODO: check if we leave cond_id or we put str(i)
                flux_estimates[cond_id] = {
                    "value": fluxes.at[reaction_with_network_name, "value"],
                    "lower_bound": fluxes.at[reaction_with_network_name, "lower_bound"],
                    "upper_bound": fluxes.at[reaction_with_network_name, "upper_bound"],
                }

                network.set_reaction_simulation_data(reaction_id, flux_estimates)

        return twin
