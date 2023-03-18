# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import pickle

from gws_core import Logger, Settings
from pandas import DataFrame

from ..network.network import Network


class Unicell:

    @classmethod
    def create_network(cls, tax_id: str = None, refresh: bool = False) -> Network:
        settings = Settings.get_instance()
        data_dir = os.path.join(settings.get_brick_data_dir(brick_name="gws_gena"), "unicell")
        if tax_id:
            file_path = os.path.join(data_dir, f"network_{tax_id}.pkl")
        else:
            file_path = os.path.join(data_dir, "network_all.pkl")
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
    def create_bigg_network(cls, refresh: bool = False):
        # Experimental method
        Logger.warning("Take care, `create_bigg_network` is an experimental method")
        path = "/lab/user/notebooks/recon/universal_model.json"
        with open(path, 'r', encoding="utf-8") as fp:
            data = json.load(fp)

        net = Network.loads(data, translate_ids=False)

        return net

    @classmethod
    def create_stoichiometric_matrix(cls, tax_id: str = None, refresh: bool = False) -> DataFrame:
        net = cls.create_network(tax_id=tax_id, refresh=refresh)
        stoich_matrix = net.create_stoichiometric_matrix()
        return stoich_matrix
