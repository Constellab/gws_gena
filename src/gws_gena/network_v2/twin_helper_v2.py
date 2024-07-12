
from typing import List, TypedDict

import numpy as np
from cobra.core import Metabolite
from gws_biota import Compartment
from gws_biota.compound.cofactor import Cofactor
from gws_core import BadRequestException
from gws_gena.context.helper.context_builder_helper import ContextBuilderHelper
from gws_gena.network_v2.network_cobra import NetworkCobra
from gws_gena.network_v2.twin_v2 import TwinV2
from pandas import DataFrame

ObsvMatrices = TypedDict("ObsvMatrices", {
    "C": DataFrame,  # stoichiometric matrix of measured fluxes
    "b": DataFrame,  # vector of measured flux values
    "r": DataFrame   # stoichiometric matrix of metabolic pool variations
})


class TwinHelperV2:

    @classmethod
    def create_steady_stoichiometric_matrix(cls, twin: TwinV2, ignore_cofactors=False) -> DataFrame:
        """
        Creates the steady stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The steady stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(twin, TwinV2):
            raise BadRequestException(
                "Cannot create the steady stoichiometric matrix. A flat model is required")
        network = twin.get_network()
        stoich_df = network.create_stoichiometric_matrix()

        # filter out non-steady metabolites
        stready_metabolites: List[Metabolite] = []
        for metabolite in network.get_metabolites():
            compartment = Compartment.get_by_bigg_id_or_go_id_or_none(metabolite.compartment)
            if compartment and compartment.is_steady:
                stready_metabolites.append(metabolite)

        # filter out cofactors
        if ignore_cofactors:
            non_co_factors = []
            for metabolite in stready_metabolites:
                if not Cofactor.is_cofactor(chebi_id=metabolite.id, name=metabolite.name,
                                            use_name_pattern=True):
                    non_co_factors.append(metabolite)

            stready_metabolites = non_co_factors

        metabolite_ids = [metabolite.id for metabolite in stready_metabolites]
        return stoich_df.loc[metabolite_ids, :]

    @classmethod
    def create_observation_matrices(cls, twin: TwinV2) -> ObsvMatrices:
        """
        Creates the observation matrices (i.e. such as C * y = b, where b is measurement vector)

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The observation matrices
        :rtype: Dict[`str`, `DataFrame`]
        """

        if not isinstance(twin, TwinV2):
            raise BadRequestException("A flat model is required")
        network = twin.get_network()
        context = twin.get_context()
        rxn_ids = network.get_reaction_ids()
        # met_ids = list(flat_net.compounds.keys())

        rxn_data_ids = [
            measure.id for measure in context.reaction_data.values()]

        C = DataFrame(
            index=rxn_data_ids,
            columns=rxn_ids,
            data=np.zeros((len(rxn_data_ids), len(rxn_ids)))
        )
        b = DataFrame(
            index=rxn_data_ids,
            columns=["target", "lb", "ub", "confidence_score"],
            data=np.zeros((len(rxn_data_ids), 4))
        )
        b.loc[:, "lb"] = NetworkCobra.REACTION_LOWER_BOUND
        b.loc[:, "ub"] = NetworkCobra.REACTION_UPPER_BOUND
        b.loc[:, "confidence_score"] = 1.0

        S_int = cls.create_steady_stoichiometric_matrix(twin)
        internal_met_ids = list(S_int.index)
        r = DataFrame(
            index=internal_met_ids,
            columns=["target", "lb", "ub", "confidence_score"],
            data=np.zeros((len(internal_met_ids), 4))
        )
        r.loc[:, "lb"] = NetworkCobra.REACTION_LOWER_BOUND
        r.loc[:, "ub"] = NetworkCobra.REACTION_UPPER_BOUND
        r.loc[:, "confidence_score"] = 1.0

        for measure in context.reaction_data.values():
            meas_id = measure.id
            for variable in measure.variables:
                ref_id = variable.reference_id
                coef = variable.coefficient
                b.loc[meas_id, :] = [
                    measure.target,
                    measure.lower_bound,
                    measure.upper_bound,
                    measure.confidence_score
                ]
                rxn_id = ref_id
                C.at[meas_id, rxn_id] = coef

        for measure in context.compound_data.values():
            for variable in measure.variables:
                ref_id = variable.reference_id
                coef = variable.coefficient
                met_id = ref_id
                r.loc[met_id, :] = [
                    measure.target,
                    measure.lower_bound,
                    measure.upper_bound,
                    measure.confidence_score
                ]
        return ObsvMatrices(C=C, b=b, r=r)

    # Method to build a twin from a sub context.
    # Useful for example if we have multiples measures for one reaction (case of multi simulations; see FBA)
    @classmethod
    def build_twin_from_sub_context(cls, base_twin: TwinV2, index: int) -> TwinV2:
        new_twin = TwinV2()

        new_twin.set_network(base_twin.get_network())

        context_builder = ContextBuilderHelper()
        new_context = context_builder.build_sub_context(
            base_twin.get_context(), index)
        new_twin.set_context(new_context)

        return new_twin
