# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import numpy as np
from scipy.linalg import null_space
from pandas import DataFrame
from typing import Dict

from gws_core import BadRequestException
from .twin import FlatTwin
from .twin_context import Variable

# ####################################################################
#
# MetaTwinService class
#
# ####################################################################

class MetaTwinService:
    
    @classmethod
    def create_fba_problem(cls, flat_twin: FlatTwin) -> Dict[str, DataFrame]:
        """
        Creates a FBA problem using a biomdel object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The FBA problem
        :rtype: `dict`
        """
        
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
        :returns: The  stroichiometric matrix
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
        :returns: The steady stroichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise BadRequestException("Cannot create the observation matrices. A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_steady_stoichiometric_matrix()

    @classmethod
    def create_non_steady_stoichiometric_matrix(cls, flat_twin: FlatTwin) -> DataFrame:
        """
        Creates the non_steady stoichiometric matrix using a twin object

        :param flat_twin: A flat twin object
        :type flat_twin: `FlatTwin`
        :returns: The non_steady stroichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(flat_twin, FlatTwin):
            raise ErBadRequestExceptionror("A flat model is required")
        flat_net = next(iter(flat_twin.networks.values()))
        return flat_net.create_non_steady_stoichiometric_matrix()

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
    def compute_nullspace(cls, A: DataFrame) -> DataFrame:
        ns = null_space(A.to_numpy())
        return DataFrame(index = A.columns, data=ns)