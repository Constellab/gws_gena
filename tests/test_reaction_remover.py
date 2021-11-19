
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, Experiment, File, IExperiment, ProcessSpec,
                      Protocol, Settings, TaskRunner, protocol_decorator)
from gws_gena import (ECTableImporter, IDTableImporter, Network,
                      NetworkImporter, ReactionRemover, Twin, TwinContext)

settings = Settings.retrieve()


@protocol_decorator("ReactionECRemoverProto")
class ReactionECRemoverProto(Protocol):
    def configure_protocol(self, _: ConfigParams) -> None:
        net_loader: ProcessSpec = self.add_process(NetworkImporter, 'net_loader')
        ec_loader: ProcessSpec = self.add_process(ECTableImporter, 'ec_loader')
        remover: ProcessSpec = self.add_process(ReactionRemover, 'remover')
        self.add_connectors([
            (net_loader >> "resource", remover << "network"),
            (ec_loader >> "resource", remover << "reaction_table"),
        ])
        self.add_interface('file1', net_loader, 'file')
        self.add_interface('file2', ec_loader, 'file')


@protocol_decorator("ReactionIDRemoverProto")
class ReactionIDRemoverProto(Protocol):
    def configure_protocol(self, _: ConfigParams) -> None:
        net_loader: ProcessSpec = self.add_process(NetworkImporter, 'net_loader')
        id_loader: ProcessSpec = self.add_process(IDTableImporter, 'id_loader')
        remover: ProcessSpec = self.add_process(ReactionRemover, 'remover')
        self.add_connectors([
            (net_loader >> "resource", remover << "network"),
            (id_loader >> "resource", remover << "reaction_table"),
        ])
        self.add_interface('file1', net_loader, 'file')
        self.add_interface('file2', id_loader, 'file')


class TestReactionremover(BaseTestCaseUsingFullBiotaDB):

    async def test_reaction_ec_remover(self):
        return
        self.print("Test reaction EC remover")
        experiment = IExperiment(ReactionECRemoverProto)
        proto = experiment.get_protocol()
        remover = proto.get_process("remover")
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        proto.set_input('file1', File(path=os.path.join(data_dir, "reaction_remover", "toy_with_added_reactions.json")))
        proto.set_input('file2', File(path=os.path.join(data_dir, "reaction_remover", "ec_table.csv")))
        await experiment.run()
        net = remover.get_output("network")

        original_net = Network.import_from_path(
            File(path=os.path.join(data_dir,  "reaction_remover", "toy_with_added_reactions.json")),
            params=ConfigParams()
        )

        self.assertEqual(len(net.reactions), 7)
        self.assertTrue("RHEA_15133_1_4_1_2" in original_net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" in original_net.reactions)
        self.assertTrue("RHEA_15133_1_4_1_2" not in net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" not in net.reactions)

    async def test_reaction_id_remover(self):
        self.print("Test reaction ID remover")
        experiment = IExperiment(ReactionIDRemoverProto)
        proto = experiment.get_protocol()
        remover = proto.get_process("remover")
        id_loader = proto.get_process("id_loader")
        id_loader.set_param('id_column_name', 'ids')
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        proto.set_input('file1', File(path=os.path.join(data_dir, "reaction_remover", "toy_with_added_reactions.json")))
        proto.set_input('file2', File(path=os.path.join(data_dir, "reaction_remover", "id_table.csv")))
        await experiment.run()
        net = remover.get_output("network")
        print(net.to_csv())

        original_net = Network.import_from_path(
            File(path=os.path.join(data_dir,  "reaction_remover", "toy_with_added_reactions.json")),
            params=ConfigParams()
        )

        #self.assertEqual(len(net.reactions), 7)
        self.assertTrue("R5_ex" not in net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" not in net.reactions)

        self.assertTrue("R5_ex" in original_net.reactions)
        self.assertTrue("RHEA_16169_6_3_1_2" in original_net.reactions)
