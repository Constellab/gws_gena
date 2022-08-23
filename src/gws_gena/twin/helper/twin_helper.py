# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, TypedDict

import efmtool
import numpy as np
import pandas
from gws_core import BadRequestException
from pandas import DataFrame
from scipy.linalg import null_space

from ..flat_twin import FlatTwin
from ...context.measure import Measure

# ####################################################################
#
# TwinHelper class
#
# ####################################################################

FBAProblem = TypedDict("FBAProblem", {
    "S": DataFrame,
    "C": DataFrame,
    "b": DataFrame,
    "C_rel": DataFrame
})

ObsvMatrices = TypedDict("ObsvMatrices", {
    "C": DataFrame,
    "b": DataFrame
})

ReducedMatrices = TypedDict("ReducedMatrices", {
    "K": DataFrame,
    "EFM": DataFrame,
})


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
            raise BadRequestException("Cannot create the stoichiometric matrix. A flat model is required")

        S = cls.create_stoichiometric_matrix(flat_twin)
        obsv_matrix = cls.create_observation_matrices(flat_twin)
        C = obsv_matrix["C"]
        b = obsv_matrix["b"]
        C_rel = S.to_numpy() @ C.to_numpy().T  # b_ref.T = S * C.T
        C_rel = DataFrame(data=C_rel.T, index=C.index, columns=S.index)
        return FBAProblem(S=S, C=C, b=b, C_rel=C_rel)

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
            raise BadRequestException("Cannot create the stoichiometric matrix. A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_stoichiometric_matrix()

    @classmethod
    def create_steady_stoichiometric_matrix(cls, flat_twin: FlatTwin, ignore_cofactors=False) -> DataFrame:
        """
        Creates the steady stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The steady stoichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("Cannot create the steady stoichiometric matrix. A flat model is required")
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
    def create_input_stoichiometric_matrix(cls, flat_twin: FlatTwin, ignore_cofactors=False) -> DataFrame:
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
    def create_output_stoichiometric_matrix(cls, flat_twin: FlatTwin, ignore_cofactors=False) -> DataFrame:
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
        measure_ids = flat_ctx.get_measure_ids()
        C = DataFrame(
            index=measure_ids,
            columns=rxn_ids,
            data=np.zeros((len(measure_ids), len(rxn_ids)))
        )
        b = DataFrame(
            index=measure_ids,
            columns=["target", "lb", "ub", "confidence_score"],
            data=np.zeros((len(measure_ids), 4))
        )
        for measure in flat_ctx.measures.values():
            meas_id = measure.id
            b.loc[meas_id, :] = [
                measure.target,
                measure.lower_bound,
                measure.upper_bound,
                measure.confidence_score
            ]
            for var_ in measure.variables:
                ref_id = var_["reference_id"]
                ref_type = var_["reference_type"]
                coef = var_["coefficient"]
                if ref_type == Measure.REACTION_REFERENCE_TYPE:
                    rxn_id = ref_id
                    C.at[meas_id, rxn_id] = coef
                else:
                    raise BadRequestException("Variables of type Metabolite are not supported in Context objects")
        return ObsvMatrices(C=C, b=b)

    @classmethod
    def compute_nullspace(cls, N: DataFrame) -> DataFrame:
        """ Compute the null space of th stoichimetric matrix """
        ns = null_space(N.to_numpy())
        return DataFrame(index=N.columns, data=ns)

    @classmethod
    def compute_elementary_flux_modes(
            cls, flat_twin: FlatTwin, reversibilities=None, ignore_cofactors=False) -> DataFrame:
        """ Compute elementary flux modes """
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
    def _compute_elementary_flux_modes_from_matrix(cls, N: DataFrame, reversibilities: List[int] = None) -> DataFrame:
        if reversibilities is None:
            reversibilities = [0] * N.shape[1]
        efms = efmtool.calculate_efms(
            N.values,
            reversibilities=reversibilities,
            reaction_names=N.columns,
            metabolite_names=N.index
        )
        column_names = [f"e{i}" for i in range(1, efms.shape[1]+1)]
        return DataFrame(index=N.columns, columns=column_names, data=efms)

    @classmethod
    def compute_reduced_matrices(cls, flat_twin: FlatTwin, use_context: bool = True, reversibilities=None,
                                 ignore_cofactors=False) -> ReducedMatrices:
        """ Compute the reduced matrices """
        EFM = TwinHelper.compute_elementary_flux_modes(
            flat_twin, reversibilities=reversibilities, ignore_cofactors=ignore_cofactors)

        Ns = TwinHelper.create_input_stoichiometric_matrix(flat_twin, ignore_cofactors=ignore_cofactors)
        Np = TwinHelper.create_output_stoichiometric_matrix(flat_twin, ignore_cofactors=ignore_cofactors)
        N = pandas.concat([Ns, Np])

        if use_context:
            obs = TwinHelper.create_observation_matrices(flat_twin)
            N = obs["C"]
        else:
            pass

        K = DataFrame(
            data=np.matmul(N.values, EFM.values),
            index=N.index,
            columns=EFM.columns
        )
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
