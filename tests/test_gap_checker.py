
import os, json
import unittest
from pandas import DataFrame

from gws.unittest import GTest
from gws.settings import Settings
settings = Settings.retrieve()

from gena.network import Compound, Reaction, Network
from gena.context import Context
from gena.biomodel import BioModel

from biota.base import DbManager as BiotaDbManager

class TestGapCheck(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()
        BiotaDbManager.use_prod_db(True)
     
    @classmethod
    def tearDownClass(cls):
        BiotaDbManager.use_prod_db(False)
        GTest.drop_tables()
    
    def test_gap_checker(self):
        pass
