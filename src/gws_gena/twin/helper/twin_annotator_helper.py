from gws_core import BadRequestException

from gws_gena.fba.fba_result import FBAResult
from gws_gena.fva.fva_result import FVAResult
from gws_gena.koa.koa_result import KOAResult
from gws_gena.network.typing.simulation_typing import SimulationDict

from ...helper.base_helper import BaseHelper
from ..flat_twin import FlatTwin
from ..twin import Twin

# ####################################################################
#
# TwinAnnotator class
#
# ####################################################################


class TwinAnnotatorHelper(BaseHelper):
    def annotate_from_fba_results(self, twin: Twin, fba_results: list[FBAResult] | list[FVAResult]):
        """
        Annotate a twin using from FBAResult
        """

        if isinstance(twin, FlatTwin):
            raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")

        flat_twin: FlatTwin = twin.flatten()
        flux_rev_mapping = flat_twin.reverse_reaction_mapping
        annotated_twin = Twin()

        for net in twin.networks.values():
            ctx_name = twin.network_contexts[net.name]
            ctx = twin.contexts[ctx_name]

            i = 0
            for fba_result in fba_results:
                fluxes = fba_result.get_fluxes_dataframe()

                for rnx_id in net.reactions:
                    rxn = net.reactions[rnx_id]
                    net_name = net.name
                    flat_rxn_id = flux_rev_mapping[net_name][rnx_id]

                    flux_estimates = rxn.get_data_slot("simulations", {})
                    flux_estimates[i] = {
                        "value": fluxes.at[flat_rxn_id, "value"],
                        "lower_bound": fluxes.at[flat_rxn_id, "lower_bound"],
                        "upper_bound": fluxes.at[flat_rxn_id, "upper_bound"],
                    }
                    rxn.add_data_slot("simulations", flux_estimates)

                i += 1

            # net.add_simulation(simulation)
            annotated_twin.add_network(net, related_context=ctx)

        return annotated_twin

    def annotate_from_fva_results(self, twin: Twin, fva_result: list[FVAResult]):
        """
        Annotate a twin using from FVAResult
        """

        return self.annotate_from_fba_results(twin, fva_result)

    def annotate_from_fba_result(
        self, twin: Twin, simulation: SimulationDict | None, fba_result: "FBAResult"
    ):
        """
        Annotate a twin using from FBAResult
        """
        if simulation is None:
            simulation = SimulationDict(
                {
                    "id": "fba_sim",
                    "name": "fba simulation",
                    "description": "Metabolic flux simulation",
                }
            )

        if isinstance(twin, FlatTwin):
            raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")

        flat_twin: FlatTwin = twin.flatten()
        flux_rev_mapping = flat_twin.reverse_reaction_mapping
        annotated_twin = Twin()

        for net in twin.networks.values():
            ctx_name = twin.network_contexts[net.name]
            ctx = twin.contexts[ctx_name]
            fluxes = fba_result.get_fluxes_dataframe()

            # cond_id = cond["id"]

            for rnx_id in net.reactions:
                rxn = net.reactions[rnx_id]
                net_name = net.name
                flat_rxn_id = flux_rev_mapping[net_name][rnx_id]

                flux_estimates = rxn.get_data_slot("simulations", {})
                # flux_estimates = {}  # rxn.get_data_slot("simulations", {}) => only one simlation is expected
                flux_estimates[simulation["id"]] = {
                    "value": fluxes.at[flat_rxn_id, "value"],
                    "lower_bound": fluxes.at[flat_rxn_id, "lower_bound"],
                    "upper_bound": fluxes.at[flat_rxn_id, "upper_bound"],
                }
                rxn.add_data_slot("simulations", flux_estimates)

            net.add_simulation(simulation)
            annotated_twin.add_network(net, related_context=ctx)

        return annotated_twin

    def annotate_from_fva_result(
        self, twin: Twin, simulation: SimulationDict | None, fva_result: FVAResult
    ):
        """
        Annotate a twin using from FVAResult
        """
        if simulation is None:
            simulation = SimulationDict(
                {
                    "id": "fva_sim",
                    "name": "fva simulation",
                    "description": "Metabolic flux simulation",
                }
            )

        return self.annotate_from_fba_result(twin, simulation, fva_result)

    def annotate_from_koa_result(self, twin: Twin, koa_result: KOAResult):
        """
        Annotate a twin using from KOAResult
        """

        if isinstance(twin, FlatTwin):
            raise BadRequestException("Cannot annotate a FlatTwin. A non-flat Twin is required")

        flat_twin: FlatTwin = twin.flatten()
        flux_rev_mapping = flat_twin.reverse_reaction_mapping
        annotated_twin = Twin()

        simulations = koa_result.get_simulations()
        if len(simulations) == 0:
            raise BadRequestException("At least one KO simulation is required")

        for net in twin.networks.values():
            ctx_name = twin.network_contexts[net.name]
            ctx = twin.contexts[ctx_name]

            for cond in simulations:
                cond_id = cond["id"]

                fluxes = koa_result.get_flux_dataframe(cond_id)
                for rnx_id in net.reactions:
                    rxn = net.reactions[rnx_id]
                    net_name = net.name
                    flat_rxn_id = flux_rev_mapping[net_name][rnx_id]
                    flux_estimates = rxn.get_data_slot("simulations", {})

                    flux_estimates[cond_id] = {
                        "value": fluxes.at[flat_rxn_id, "value"],
                        "lower_bound": fluxes.at[flat_rxn_id, "lower_bound"],
                        "upper_bound": fluxes.at[flat_rxn_id, "upper_bound"],
                    }

                    rxn.add_data_slot("simulations", flux_estimates)

            net.add_simulation(simulations[0])
            annotated_twin.add_network(net, related_context=ctx)

        return annotated_twin
