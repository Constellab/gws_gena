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
    def create_network(cls, tax_id: str = None, refresh: bool = False) -> Network:
        data_dir = os.path.join(settings.get_brick_data_dir(brick_name="gws_gena"), "unicell")
        file_path = os.path.join(data_dir, "network.pkl")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        net = None
        if not refresh:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as fp:
                    net = pickle.load(fp)

        if net is None:
            net = Network.from_biota(tax_id=tax_id)
            with open(file_path, 'wb') as fp:
                pickle.dump(net, fp)
        return net

    @classmethod
    def create_stoichiometric_matrix(cls, tax_id: str = None, refresh: bool = False) -> DataFrame:
        net = cls.create_network(tax_id=tax_id, refresh=refresh)
        stoich_matrix = net.create_stoichiometric_matrix()
        return stoich_matrix
