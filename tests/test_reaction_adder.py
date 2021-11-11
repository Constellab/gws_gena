
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, Experiment, File, IExperiment, ProcessSpec,
                      Protocol, Settings, TaskTester, protocol_decorator)
from gws_gena import (ECTableImporter, IDTableImporter, NetworkImporter,
                      ReactionAdder, Twin, TwinContext)

settings = Settings.retrieve()


@protocol_decorator("ReactionECAdderProto")
class ReactionECAdderProto(Protocol):
    def configure_protocol(self, _: ConfigParams) -> None:
        net_loader: ProcessSpec = self.add_process(NetworkImporter, 'net_loader')
        ec_loader: ProcessSpec = self.add_process(ECTableImporter, 'ec_loader')
        adder: ProcessSpec = self.add_process(ReactionAdder, 'adder')
        self.add_connectors([
            (net_loader >> "resource", adder << "network"),
            (ec_loader >> "resource", adder << "reaction_table"),
        ])
        self.add_interface('file1', net_loader, 'file')
        self.add_interface('file2', ec_loader, 'file')


@protocol_decorator("ReactionIDAdderProto")
class ReactionIDAdderProto(Protocol):
    def configure_protocol(self, _: ConfigParams) -> None:
        net_loader: ProcessSpec = self.add_process(NetworkImporter, 'net_loader')
        id_loader: ProcessSpec = self.add_process(IDTableImporter, 'id_loader')
        adder: ProcessSpec = self.add_process(ReactionAdder, 'adder')
        self.add_connectors([
            (net_loader >> "resource", adder << "network"),
            (id_loader >> "resource", adder << "reaction_table"),
        ])
        self.add_interface('file1', net_loader, 'file')
        self.add_interface('file2', id_loader, 'file')


class TestReactionAdder(BaseTestCaseUsingFullBiotaDB):

    async def test_reaction_ec_adder(self):
        self.print("Test reaction EC adder")
        experiment = IExperiment(ReactionECAdderProto)
        proto = experiment.get_protocol()
        adder = proto.get_process("adder")
        adder.set_param("tax_id", "2759")  # eukaryota
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        proto.set_input('file1', File(path=os.path.join(data_dir, "toy", "toy.json")))
        proto.set_input('file2', File(path=os.path.join(data_dir, "reaction_adder", "ec_table.csv")))
        await experiment.run()
        net = adder.get_output("network")
        # print(net.to_csv())
        self.assertEqual(len(net.reactions), 9)
        self.assertTrue("RHEA_15133_1_4_1_2" in net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" in net.reactions)

        # file_path = os.path.join(data_dir, "reaction_adder", "toy_with_added_ec.json")
        # with open(file_path, 'w') as f:
        #     json.dump(net.dumps(), f)

    async def test_reaction_id_adder(self):
        self.print("Test reaction ID adder")
        experiment = IExperiment(ReactionIDAdderProto)
        proto = experiment.get_protocol()
        adder = proto.get_process("adder")
        id_loader = proto.get_process("id_loader")
        id_loader.set_param('id_column_name', 'rhea_id')
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        proto.set_input('file1', File(path=os.path.join(data_dir, "toy", "toy.json")))
        proto.set_input('file2', File(path=os.path.join(data_dir, "reaction_adder", "rhea_id_table.csv")))
        await experiment.run()
        net = adder.get_output("network")
        # print(net.to_csv())
        self.assertEqual(len(net.reactions), 8)
        self.assertTrue("RHEA_16505_4_1_3_40" in net.reactions)

        # file_path = os.path.join(data_dir, "reaction_adder", "toy_with_added_id.json")
        # with open(file_path, 'w') as f:
        #     json.dump(net.dumps(), f)
