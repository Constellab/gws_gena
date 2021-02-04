
import os, json
import asyncio
import unittest

from gws.settings import Settings
from gws.model import Protocol, Experiment
from gws.controller import Controller

from biota.db.compound import Compound
from biota.db.enzyme import Enzyme
from biota.db.reaction import Reaction, ReactionEnzyme
from biota.db.enzyme import Enzyme, EnzymeBTO

from gena.recon import Datatable, DataImporter, CellMaker, Cell

def insert_data(data):
    r = Reaction(data=data, direction="UN")
    r.save()

    s = {}
    p = {}
    for k in data["substrates"]:
        s[k] = Compound(title="", chebi_id=k)
        s[k].save()
        r.substrates.add(s[k])

    for k in data["products"]:
        p[k] = Compound(title="", chebi_id=k)
        p[k].save()
        r.products.add(p[k])

    e = {}
    for k in data["enzymes"]:
        e[k] = Enzyme(ec_number=k)
        e[k].save()
        r.enzymes.add(e[k])

    r.save()


class TestImporter(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Cell.drop_table()
        Cell.create_table()
        pass

    @classmethod
    def tearDownClass(cls): 
        pass
    
    def test_recon(self):
        return
        #create_db()
        
        settings = Settings.retrieve()
        test_dir = settings.get_dir("gena:testdata_dir")

        importer = DataImporter()
        cell_maker = CellMaker()
        proto = Protocol(
            title = "cell_maker_protocol",
            processes = {
                'importer': importer,
                'cell_maker': cell_maker
            },
            connectors = [
                importer>>'datatable' | cell_maker<<'datatable'
            ],
            interfaces = {},
            outerfaces = {'cell': cell_maker>>'cell'}
        )

        cell_maker.set_param("tax_ids", [4753, 4754, 42068, 263815])
        importer.set_param("file_path", os.path.join(test_dir, "./ec_data.xlsx"))
        importer.set_param("header", 0)
        importer.set_param("ec_column_name", "EC Number")

        # tests (on end)
        def _on_end(*args, **kwargs):
            dt = importer.output['datatable']
            self.assertIsInstance(dt, Datatable)
            self.assertEquals(dt.get_ec_numbers()[0], "1.4.1.2")

            c = proto.output["cell"]
            ez = c.enzymes
            #self.assertEquals(len(ez), 1398)
            self.assertEquals(len(ez), 15)

            Q = c.reactions
            self.assertEquals(len(Q), 15)
            print(Q[3].data)
            print(Q[0].direction)
            
            #print(c.as_json(stringify=True, prettify=True, bare=True))
            
            #with open(os.path.join(test_dir, "./cell.json"), "r") as fp:
            #    txt = fp.read()
            #    expected = json.loads(txt)
            #    self.assertEquals(c.as_json(bare=True), expected)

        e = proto.create_experiment()
        e.on_end( _on_end )
            
 
        asyncio.run( e.run() )

 

    
        