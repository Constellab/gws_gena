
import os
import asyncio
import unittest

from gws.settings import Settings
from gws.model import Protocol, Experiment
from gws.controller import Controller

from biota.db.compound import Compound
from biota.db.enzyme import Enzyme
from biota.db.reaction import Reaction, ReactionEnzyme
from biota.db.enzyme import Enzyme, EnzymeBTO

from gena.recon import Datatable, DataImporter, CellMaker, Cell, CellViewModel

def insert_data(data):
    r = Reaction(data=data, direction="UN")
    r.save()

    s = {}
    p = {}
    for k in data["substrates"]:
        s[k] = Compound(name="", chebi_id=k)
        s[k].save()
        r.substrates.add(s[k])

    for k in data["products"]:
        p[k] = Compound(name="", chebi_id=k)
        p[k].save()
        r.products.add(p[k])

    e = {}
    for k in data["enzymes"]:
        e[k] = Enzyme(ec_number=k)
        e[k].save()
        r.enzymes.add(e[k])

    r.save()

def create_db():
    data = {
            'entry': 'RHEA:15133', 
            'definition': 'H2O + L-glutamate + NAD(+) = 2-oxoglutarate + H(+) + NADH + NH4(+)', 
            'equation': {'substrates': {'CHEBI:15377': 1, 'CHEBI:29985': 1, 'CHEBI:57540': 1}, 
            'products': {'CHEBI:16810': 1, 'CHEBI:15378': 1, 'CHEBI:57945': 1, 'CHEBI:28938': 1}}, 
            'enzymes': ['1.4.1.2', '1.4.1.3'], 
            'source_equation': 'CHEBI:15377 + CHEBI:29985 + CHEBI:57540 = CHEBI:16810 + CHEBI:15378 + CHEBI:57945 + CHEBI:28938', 
            'substrates': ['CHEBI:15377', 'CHEBI:29985', 'CHEBI:57540'], 
            'products': ['CHEBI:16810', 'CHEBI:15378', 'CHEBI:57945', 'CHEBI:28938'], 
            'COMMENT': 'RHEA:15133 part of RHEA:13753)\n'
    }
    insert_data(data)

    
    data={
            'entry': 'RHEA:24304', 
            'definition': 'glycine + H(+) + N(6)-lipoyl-L-lysyl-[glycine-cleavage complex H protein] = (R)-N(6)-(S(8)-aminomethyldihydrolipoyl)-L-lysyl-[glycine-cleavage complex H protein] + CO2', 
            'equation': {'substrates': {'CHEBI:57305': 1, 'CHEBI:15378': 1, 'CHEBI:83099': 1}, 
            'products': {'CHEBI:83143': 1, 'CHEBI:16526': 1}}, 
            'enzymes': ['1.4.4.2'], 'source_equation': 'CHEBI:57305 + CHEBI:15378 + CHEBI:83099 = CHEBI:83143 + CHEBI:16526', 
            'substrates': ['CHEBI:57305', 'CHEBI:15378', 'CHEBI:83099'], 
            'products': ['CHEBI:83143', 'CHEBI:16526']}
    insert_data(data)

    data={
            'entry': 'RHEA:21824', 
            'definition': '2-oxoglutarate + L-aspartate = L-glutamate + oxaloacetate', 
            'equation': {'substrates': {'CHEBI:16810': 1, 'CHEBI:29991': 1}, 
            'products': {'CHEBI:29985': 1, 'CHEBI:16452': 1}}, 
            'enzymes': ['2.6.1.1'], 
            'source_equation': 'CHEBI:16810 + CHEBI:29991 = CHEBI:29985 + CHEBI:16452', 
            'substrates': ['CHEBI:16810', 'CHEBI:29991'], 
            'products': ['CHEBI:29985', 'CHEBI:16452']}
    insert_data(data)

    data={
            'entry': 'RHEA:13237', 
            'definition': 'D-fructose 6-phosphate + L-glutamine = D-glucosamine 6-phosphate + L-glutamate', 
            'equation': {'substrates': {'CHEBI:61527': 1, 'CHEBI:58359': 1}, 
            'products': {'CHEBI:58725': 1, 'CHEBI:29985': 1}}, 
            'enzymes': ['2.6.1.16'], 
            'source_equation': 'CHEBI:61527 + CHEBI:58359 = CHEBI:58725 + CHEBI:29985', 
            'substrates': ['CHEBI:61527', 'CHEBI:58359'], 
            'products': ['CHEBI:58725', 'CHEBI:29985']}
    insert_data(data)

class TestImporter(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Cell.drop_table()
        Reaction.drop_table()
        Enzyme.drop_table()
        Enzyme.drop_table()
        Compound.drop_table()

        Cell.create_table()
        Compound.create_table()
        Enzyme.create_table()
        Reaction.create_table()
        Enzyme.create_table()
        pass

    @classmethod
    def tearDownClass(cls): 
        # Reaction.drop_table()
        # Enzyme.drop_table()
        # Enzyme.drop_table()
        # Compound.drop_table()
        pass
    
    def test_cell(self):
        create_db()


    def test_recon(self):
        async def _import_ec(self):
            settings = Settings.retrieve()
            test_dir = settings.get_dir("gena:testdata_dir")

            # importer
            importer = DataImporter()
            importer.set_param("file_path", os.path.join(test_dir, "./ec_data.xlsx"))
            importer.set_param("header", 0)
            importer.set_param("ec_column_name", "EC Number")
            
            # cell maker
            cell_maker = CellMaker()
            cell_maker.set_param("tax_ids", [4753, 4754, 42068, 263815])
            # protocol
            proto = Protocol(
                name = "cell_maker_protocol",
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

            proto.set_active_experiment(Experiment())

            # tests (on end)
            def _on_end(*args, **kwargs):
                dt = importer.output['datatable']
                self.assertIsInstance(dt, Datatable)
                self.assertEquals(dt.get_ec_numbers()[0], "1.4.1.2")

                c = proto.output["cell"]
                ez = c.enzymes
                #self.assertEquals(len(ez), 1398)
                self.assertEquals(len(ez), 4)

                Q = c.reactions
                self.assertEquals(len(Q), 4)
                print(Q[3].data)
                print(Q[0].direction)

                vm = CellViewModel(model=c)
                print(vm.render())

                import json
                r = json.loads(vm.render())
                
                with open(os.path.join(test_dir, "./cell.json"), "r") as fp:
                    txt = fp.read()
                    expected = json.loads(txt)
                    self.assertEquals(r, expected)

            proto.on_end( _on_end )
            
            await proto.run()

        asyncio.run( _import_ec(self) )

 

    
        