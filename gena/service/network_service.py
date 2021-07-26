# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import numpy as np
from scipy.linalg import null_space
from pandas import DataFrame
from typing import Dict

from gws.exception.bad_request_exception import BadRequestException
from ..network import Network

# ####################################################################
#
# BioModelService class
#
# ####################################################################

class NetworkService:

    @classmethod
    def create_stoichiometric_matrix(cls, net: Network) -> DataFrame:
        """
        Creates the full stoichiometric matrix of a network

        :param net: A network
        :type net: `Network`
        :returns: The  stroichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(net, Network):
            raise BadRequestException("A network is required")
        
        return net.create_stoichiometric_matrix()

    @classmethod
    def create_steady_stoichiometric_matrix(cls, net: Network) -> DataFrame:
        """
        Creates the steady stoichiometric matrix of a network

        :param net: A network
        :type net: `Network`
        :returns: The steady stroichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(net, Network):
            raise BadRequestException("A netwok is required")
        return net.create_steady_stoichiometric_matrix()

    @classmethod
    def create_non_steady_stoichiometric_matrix(cls, net: Network) -> DataFrame:
        """
        Creates the non-steady stoichiometric of a network

        :param net: A network
        :type net: `Network`
        :returns: The non-steady stroichiometric matrix
        :rtype: `DataFrame`
        """

        if not isinstance(net, Network):
            raise BadRequestException("A network is required")
        flat_net = next(iter(flat_biomodel.networks.values()))
        return flat_net.create_non_steady_stoichiometric_matrix()

    @classmethod
    def __compute_nullspace(cls, A: DataFrame) -> DataFrame:
        ns = null_space(A.to_numpy())
        return DataFrame(index = A.columns, data=ns)