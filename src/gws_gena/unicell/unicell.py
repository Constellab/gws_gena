# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import pickle

import pandas
from gws_core import Settings
from pandas import DataFrame

from ..network.network import Network

settings = Settings.get_instance()


class Unicell:

    @classmethod
    def create_network(cls) -> Network:
        net = Network.from_biota()
        return net

    @classmethod
    def create_stoichiometric_matrix(cls, load_if_exists: bool = False) -> DataFrame:
        data_dir = os.path.join(settings.get_brick_data_dir(brick_name="gws_gena"), "unicell")
        file_path = os.path.join(data_dir, "stoichiometric_matrix.pkl")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        is_loaded = False
        if load_if_exists:
            if os.path.exists(file_path):
                stoich_matrix = pandas.read_pickle(file_path)
                is_loaded = True

        if not is_loaded:
            net = cls.create_network()
            stoich_matrix = net.create_stoichiometric_matrix()
            stoich_matrix.to_pickle(file_path)

        return stoich_matrix

    # @classmethod
    # def create_incidence_matrix(cls, load_if_exists: bool = False) -> DataFrame:
    #     stoich_matrix = cls.create_stoichiometric_matrix(load_if_exists=load_if_exists)
    #     return np.abs(stoich_matrix.to_numpy()) > 0

    # @classmethod
    # def create_neg_incidence_matrix(cls, load_if_exists: bool = False) -> DataFrame:
    #     stoich_matrix = cls.create_stoichiometric_matrix(load_if_exists=load_if_exists)
    #     return np.abs(stoich_matrix.to_numpy()) > 0