# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List
import numpy as np
import pandas
from pandas import DataFrame
from scipy.linalg import null_space
import efmtool

from gws_core import BadRequestException
from .twin import FlatTwin
from .twin_context import Variable

# ####################################################################
#
# TwinService class
#
# ####################################################################

class TwinService:
    
    @classmethod
    def create_fba_problem(cls, flat_twin: FlatTwin) -> Dict[str, DataFrame]:
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

        return {
            "S": S,
            "C": obsv_matrix["C"],
            "b": obsv_matrix["b"]
        }
    
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
    def create_steady_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
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
        return flat_net.create_steady_stoichiometric_matrix()

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
    def compute_input_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
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
        return flat_net.compute_input_stoichiometric_matrix()

    @classmethod
    def compute_output_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
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
        return flat_net.compute_output_stoichiometric_matrix()

    @classmethod
    def create_observation_matrices(cls, flat_twin: FlatTwin) -> Dict[str, DataFrame]:
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
            index = measure_ids,
            columns = rxn_ids,
            data = np.zeros((len(measure_ids),len(rxn_ids)))
        )
        b = DataFrame(
            index = measure_ids,
            columns = ["target", "lb", "ub", "confidence_score"],
            data = np.zeros((len(measure_ids),4))
        )
        for k in flat_ctx.measures:
            measure = flat_ctx.measures[k]
            meas_id = measure.id
            b.loc[meas_id, :] = [
                measure.target, 
                measure.lower_bound, 
                measure.upper_bound,
                measure.confidence_score
            ]
            for v in measure.variables:
                ref_id = v.reference_id
                ref_type = v.reference_type
                coef = v.coefficient
                if ref_type == Variable.REACTION_REFERENCE_TYPE:
                    rxn_id = ref_id
                    C.at[meas_id, rxn_id] = coef
                else:
                    raise BadRequestException("Variables of type metabolite/compound are not supported in context")
        return {
            "C": C,
            "b": b
        }

    @classmethod
    def compute_nullspace(cls, N: DataFrame) -> DataFrame:
        ns = null_space(N.to_numpy())
        return DataFrame(index = N.columns, data=ns)

    @classmethod
    def compute_elementary_flux_modes(cls, flat_twin: FlatTwin) -> DataFrame:
        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("A flat model is required")
        N = cls.create_steady_stoichiometric_matrix(flat_twin)
        return cls._compute_elementary_flux_modes_from_matrix(N)

    @classmethod
    def _compute_elementary_flux_modes_from_matrix(cls, N: DataFrame, reversibilities: List[int] = None) -> DataFrame:
        if reversibilities is None:
            reversibilities = [0] * N.shape[1]
        efms = efmtool.calculate_efms(
            N.values,
            reversibilities = reversibilities,
            reaction_names = N.columns,
            metabolite_names = N.index
        )
        column_names = [ f"e{i}" for i in range(1,efms.shape[1]+1) ]
        return DataFrame(index=N.columns, columns=column_names, data=efms)

    @classmethod
    def compute_reduced_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
        E = TwinService.compute_elementary_flux_modes(flat_twin)
        Ns = TwinService.compute_input_stoichiometric_matrix(flat_twin)
        Np = TwinService.compute_output_stoichiometric_matrix(flat_twin)
        N = pandas.concat([Ns, Np])
        K = DataFrame(
            data=np.matmul(N.values, E.values),
            index=N.index,
            columns=E.columns
        )
        return K



