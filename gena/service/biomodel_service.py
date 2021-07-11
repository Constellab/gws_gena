# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import numpy as np
from scipy.linalg import null_space
from pandas import DataFrame
from typing import Dict

from gws.logger import Error

# ####################################################################
#
# BioModelService class
#
# ####################################################################

class BioModelService:
    
    @classmethod
    def create_fba_problem(cls, flat_biomodel: 'FlatBioModel') -> Dict[str, DataFrame]:
        """
        Creates a FBA problem using a biomdel object

        :param flat_biomodel: A flat biomodel object
        :type flat_biomodel: `FlatBioModel`
        :returns: The FBA problem
        :rtype: `dict`
        """
        
        S = cls.create_stoichiometric_matrix(flat_biomodel)
        obsv_matrix = cls.create_observation_matrices(flat_biomodel)

        return {
            "S": S,
            "C": obsv_matrix["C"],
            "b": obsv_matrix["b"]
        }
    
    @classmethod
    def create_stoichiometric_matrix(cls, flat_biomodel: 'FlatBioModel') -> DataFrame:
        """
        Creates the full stoichiometric matrix using a biomodel object

        :param flat_biomodel: A flat biomodel object
        :type flat_biomodel: `FlatBioModel`
        :returns: The  stroichiometric matrix
        :rtype: `DataFrame`
        """

        from gena.biomodel import FlatBioModel
        if not isinstance(flat_biomodel, FlatBioModel):
            raise Error("BioModelService", "create_observation_matrices", "A flat model is required")
        
        flat_net = next(iter(flat_biomodel.networks.values()))
        return flat_net.create_stoichiometric_matrix()

    @classmethod
    def create_steady_stoichiometric_matrix(cls, flat_biomodel: 'FlatBioModel') -> DataFrame:
        """
        Creates the steady stoichiometric matrix using a biomodel object

        :param flat_biomodel: A flat biomodel object
        :type flat_biomodel: `FlatBioModel`
        :returns: The steady stroichiometric matrix
        :rtype: `DataFrame`
        """

        from gena.biomodel import FlatBioModel
        if not isinstance(flat_biomodel, FlatBioModel):
            raise Error("BioModelService", "create_observation_matrices", "A flat model is required")
        
        flat_net = next(iter(flat_biomodel.networks.values()))
        return flat_net.create_steady_stoichiometric_matrix()

    @classmethod
    def create_non_steady_stoichiometric_matrix(cls, flat_biomodel: 'FlatBioModel') -> DataFrame:
        """
        Creates the non_steady stoichiometric matrix using a biomodel object

        :param flat_biomodel: A flat biomodel object
        :type flat_biomodel: `FlatBioModel`
        :returns: The non_steady stroichiometric matrix
        :rtype: `DataFrame`
        """

        from gena.biomodel import FlatBioModel
        if not isinstance(flat_biomodel, FlatBioModel):
            raise Error("BioModelService", "create_observation_matrices", "A flat model is required")
        
        flat_net = next(iter(flat_biomodel.networks.values()))
        return flat_net.create_non_steady_stoichiometric_matrix()

    @classmethod
    def create_observation_matrices(cls, flat_biomodel: 'FlatBioModel') -> Dict[str, DataFrame]:
        """
        Creates the observation matrices (i.e. such as C * y = b, where b is measurement vector)

        :param flat_biomodel: A flat biomodel object
        :type flat_biomodel: `FlatBioModel`
        :returns: The observation matrices
        :rtype: Dict[`str`, `DataFrame`]
        """

        from gena.biomodel import FlatBioModel
        from gena.context import Variable
        
        if not isinstance(flat_biomodel, FlatBioModel):
            raise Error("BioModelService", "create_observation_matrices", "A flat model is required")
        
        flat_net = next(iter(flat_biomodel.networks.values()))
        flat_ctx = next(iter(flat_biomodel.contexts.values()))

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
                    raise Error("BioModelService", "create_observation_matrices", "Variables of type metabolite/compound are not supported in context")
        
        return {
            "C": C,
            "b": b
        }
        #return C, b

    # @classmethod
    # def extract_steady_stoichiometric_matrix(cls, S_full: DataFrame) -> DataFrame:
    #     """
    #     Extracts the steady stoichiometric matrix

    #     :param S_full: A full stoichiometric matrix
    #     :type S_full: `DataFrame`
    #     :returns: The steady stoichiometric matrix
    #     :rtype: `DataFrame`
    #     """

    #     from gena.network import Network
        
    #     comp_names = S_full.index
    #     selected_comp_names = []
    #     for name in comp_names:
    #         if Network.is_intracell(name):
    #             selected_comp_names.append(name)
                
    #     return S_full.loc[selected_comp_names, :]

    # @classmethod
    # def extract_non_steady_stoichiometric_matrix(cls, S_full: DataFrame) -> DataFrame:
    #     """
    #     Extracts the non-steady stoichiometric matrix

    #     :param S_full: A full stoichiometric matrix
    #     :type S_full: `DataFrame`
    #     :returns: The non-steady stoichiometric matrix
    #     :rtype: `DataFrame`
    #     """

    #     from gena.network import Network

    #     comp_names = S_full.index
    #     selected_comp_names = []
    #     for name in comp_names:
    #         if Network.is_extracell(name, include_biomass=include_biomass):
    #             selected_comp_names.append(name)
                
    #     return S_full.loc[selected_comp_names, :]

    @classmethod
    def compute_nullspace(cls, A: DataFrame) -> DataFrame:
        ns = null_space(A.to_numpy())
        return DataFrame(index = A.columns, data=ns)