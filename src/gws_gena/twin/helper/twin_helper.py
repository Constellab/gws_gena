from typing import TypedDict

import efmtool
import numpy as np
import pandas
from gws_core import BadRequestException
from pandas import DataFrame
from scipy.linalg import null_space

from ...context.helper.context_builder_helper import ContextBuilderHelper
from ...network.reaction.reaction import Reaction
from ..flat_twin import FlatTwin
from ..twin import Twin

# ####################################################################
#
# TwinHelper class
#
# ####################################################################


class FBAProblem(TypedDict):
    S: DataFrame
    C: DataFrame
    b: DataFrame
    r: DataFrame
    C_rel: DataFrame


class ObsvMatrices(TypedDict):
    C: DataFrame
    b: DataFrame
    r: DataFrame


class ReducedMatrices(TypedDict):
    K: DataFrame
    EFM: DataFrame


class TwinHelper:
    @classmethod
    def create_fba_problem(cls, flat_twin: FlatTwin) -> FBAProblem:
        """
        Creates a FBA problem using a biomdel object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The FBA problem
        :rtype: `dict`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException(
                "Cannot create the stoichiometric matrix. A flat model is required"
            )

        S = cls.create_stoichiometric_matrix(flat_twin)
        obsv_matrix = cls.create_observation_matrices(flat_twin)
        C = obsv_matrix["C"]
        r = obsv_matrix["r"]
        b = obsv_matrix["b"]
        C_rel = S.to_numpy() @ C.to_numpy().T  # b_ref.T = S * C.T
        C_rel = DataFrame(data=C_rel.T, index=C.index, columns=S.index)
        return FBAProblem(S=S, C=C, b=b, r=r, C_rel=C_rel)

    @classmethod
    def create_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
        """
        Creates the full stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The  stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException(
                "Cannot create the stoichiometric matrix. A flat model is required"
            )
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_stoichiometric_matrix()

    @classmethod
    def create_steady_stoichiometric_matrix(
        cls, flat_twin: FlatTwin, ignore_cofactors=False
    ) -> DataFrame:
        """
        Creates the steady stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The steady stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException(
                "Cannot create the steady stoichiometric matrix. A flat model is required"
            )
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_steady_stoichiometric_matrix(ignore_cofactors=ignore_cofactors)

    @classmethod
    def create_non_steady_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
        """
        Creates the non_steady stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The non_steady stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_non_steady_stoichiometric_matrix()

    @classmethod
    def create_input_stoichiometric_matrix(
        cls, flat_twin: FlatTwin, ignore_cofactors=False
    ) -> DataFrame:
        """
        Creates the input-substrate stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The input-substrate stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_input_stoichiometric_matrix(ignore_cofactors=ignore_cofactors)

    @classmethod
    def create_output_stoichiometric_matrix(
        cls, flat_twin: FlatTwin, ignore_cofactors=False
    ) -> DataFrame:
        """
        Creates the output-product stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The output-product stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_output_stoichiometric_matrix(ignore_cofactors=ignore_cofactors)

    @classmethod
    def create_observation_matrices(cls, flat_twin: FlatTwin) -> ObsvMatrices:
        """
        Creates the observation matrices (i.e. such as C * y = b, where b is measurement vector)

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The observation matrices
        :rtype: Dict[`str`, `DataFrame`]
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        flat_ctx = next(iter(flat_twin.contexts.values()))
        rxn_ids = list(flat_net.reactions.keys())
        # met_ids = list(flat_net.compounds.keys())

        rxn_data_ids = [measure.id for measure in flat_ctx.reaction_data.values()]

        C = DataFrame(
            index=rxn_data_ids, columns=rxn_ids, data=np.zeros((len(rxn_data_ids), len(rxn_ids)))
        )
        b = DataFrame(
            index=rxn_data_ids,
            columns=["target", "lb", "ub", "confidence_score"],
            data=np.zeros((len(rxn_data_ids), 4)),
        )
        b.loc[:, "lb"] = Reaction.LOWER_BOUND
        b.loc[:, "ub"] = Reaction.UPPER_BOUND
        b.loc[:, "confidence_score"] = 1.0

        S_int = cls.create_steady_stoichiometric_matrix(flat_twin)
        internal_met_ids = list(S_int.index)
        r = DataFrame(
            index=internal_met_ids,
            columns=["target", "lb", "ub", "confidence_score"],
            data=np.zeros((len(internal_met_ids), 4)),
        )
        r.loc[:, "lb"] = Reaction.LOWER_BOUND
        r.loc[:, "ub"] = Reaction.UPPER_BOUND
        r.loc[:, "confidence_score"] = 1.0

        for measure in flat_ctx.reaction_data.values():
            meas_id = measure.id
            for variable in measure.variables:
                ref_id = variable.reference_id
                coef = variable.coefficient
                b.loc[meas_id, :] = [
                    measure.target,
                    measure.lower_bound,
                    measure.upper_bound,
                    measure.confidence_score,
                ]
                rxn_id = ref_id
                C.at[meas_id, rxn_id] = coef

        for measure in flat_ctx.compound_data.values():
            for variable in measure.variables:
                ref_id = variable.reference_id
                coef = variable.coefficient
                met_id = ref_id
                r.loc[met_id, :] = [
                    measure.target,
                    measure.lower_bound,
                    measure.upper_bound,
                    measure.confidence_score,
                ]
        return ObsvMatrices(C=C, b=b, r=r)

    @classmethod
    def compute_nullspace(cls, N: DataFrame) -> DataFrame:
        """Compute the null space of th stoichimetric matrix"""
        ns = null_space(N.to_numpy())
        return DataFrame(index=N.columns, data=ns)

    @classmethod
    def compute_elementary_flux_modes(
        cls, flat_twin: FlatTwin, reversibilities=None, ignore_cofactors=False
    ) -> DataFrame:
        """Compute elementary flux modes"""
        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat model is required")
        N = cls.create_steady_stoichiometric_matrix(flat_twin, ignore_cofactors=ignore_cofactors)

        # Nn = cls.create_non_steady_stoichiometric_matrix(flat_twin)
        # idx = Nn.any(axis=0)
        # reversibilities = [0] * N.shape[1]
        # for k in range(idx.shape[0]):
        #     if idx.iloc[k]:
        #         reversibilities[k] = 1

        return cls._compute_elementary_flux_modes_from_matrix(N, reversibilities=reversibilities)

    @classmethod
    def _compute_elementary_flux_modes_from_matrix(
        cls, N: DataFrame, reversibilities: list[int] | None = None
    ) -> DataFrame:
        if reversibilities is None:
            reversibilities = [0] * N.shape[1]
        efms = efmtool.calculate_efms(
            N.values,
            reversibilities=reversibilities,
            reaction_names=N.columns,
            metabolite_names=N.index,
        )
        column_names = [f"e{i}" for i in range(1, efms.shape[1] + 1)]
        return DataFrame(index=N.columns, columns=column_names, data=efms)

    @classmethod
    def compute_reduced_matrices(
        cls,
        flat_twin: FlatTwin,
        use_context: bool = True,
        reversibilities=None,
        ignore_cofactors=False,
    ) -> ReducedMatrices:
        """Compute the reduced matrices"""
        EFM = TwinHelper.compute_elementary_flux_modes(
            flat_twin, reversibilities=reversibilities, ignore_cofactors=ignore_cofactors
        )

        Ns = TwinHelper.create_input_stoichiometric_matrix(
            flat_twin, ignore_cofactors=ignore_cofactors
        )
        Np = TwinHelper.create_output_stoichiometric_matrix(
            flat_twin, ignore_cofactors=ignore_cofactors
        )
        N = pandas.concat([Ns, Np])

        if use_context:
            obs = TwinHelper.create_observation_matrices(flat_twin)
            N = obs["C"]
        else:
            pass

        K = DataFrame(data=np.matmul(N.values, EFM.values), index=N.index, columns=EFM.columns)
        # remove all zero rows
        K = K.loc[K.any(axis=1), :]
        K = K.loc[:, K.any(axis=0)]

        return ReducedMatrices(K=K, EFM=EFM)

    # @classmethod
    # def compute_reduced_matrices(cls, flat_twin: FlatTwin) -> DataFrame:
    #     EFM = TwinHelper.compute_elementary_flux_modes(flat_twin)
    #     Ns = TwinHelper.create_input_stoichiometric_matrix(flat_twin)
    #     Np = TwinHelper.create_output_stoichiometric_matrix(flat_twin)
    #     N = pandas.concat([Ns, Np])
    #     print(N)

    #     obs = TwinHelper.create_observation_matrices(flat_twin)
    #     C = obs["C"]
    #     print(C)

    #     K = DataFrame(
    #         data=np.matmul(C, E.values),
    #         index=C.index,
    #         columns=E.columns
    #     )

    #     # remove all zero rows
    #     K = K.loc[K.any(axis=1), :]
    #     K = K.loc[:, K.any(axis=0)]

    #     return ReducedMatrices(K=K, EFM=EFM)

    # Method to build a twin from a sub context.
    # Useful for example if we have multiples measures for one reaction (case of multi simulations; see FBA)
    def build_twin_from_sub_context(self, base_twin: Twin, index: int) -> Twin:
        new_twin = Twin()

        network = next(iter(base_twin.networks.values()))
        new_twin.add_network(network)

        base_context = next(iter(base_twin.contexts.values()))
        new_context = ContextBuilderHelper.build_sub_context(self, base_context, index)
        new_twin.add_context(new_context, related_network=network)

        return new_twin
