
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, Experiment, File, IExperiment, ProcessSpec,
                      Protocol, Settings, protocol_decorator)
from gws_gena import Network, NetworkImporter, NetworkMerger, Twin, Context

settings = Settings.retrieve()


@protocol_decorator("MergerProtocol")
class MergerProtocol(Protocol):
    def configure_protocol(self, _: ConfigParams) -> None:
        loader_1: ProcessSpec = self.add_process(NetworkImporter, 'loader_1')
        loader_2: ProcessSpec = self.add_process(NetworkImporter, 'loader_2')
        merger: ProcessSpec = self.add_process(NetworkMerger, 'merger')

        self.add_connectors([
            (loader_1 >> "target", merger << "network_1"),
            (loader_2 >> "target", merger << "network_2")
        ])

        self.add_interface('file1', loader_1, 'source')
        self.add_interface('file2', loader_2, 'source')


class TestMerge(BaseTestCaseUsingFullBiotaDB):

    async def test_merger(self):
        self.print("Test Merger")

        experiment = IExperiment(MergerProtocol)
        proto = experiment.get_protocol()
        merger = proto.get_process("merger")

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        file1 = File(path=os.path.join(data_dir, "recon", "recon_net.json"))
        file2 = File(path=os.path.join(data_dir, "network_merger", "addon.json"))
        proto.set_input('file1', file1)
        proto.set_input('file2', file2)

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        result_dir = os.path.join(data_dir, "network_merger")

        await experiment.run()
        net_merged = merger.get_output("network")

        net1 = NetworkImporter.call(file1, ConfigParams())
        net2 = NetworkImporter.call(file2, ConfigParams())
        n1 = len(net1.reactions)
        n2 = len(net2.reactions)
        n_total = len(net_merged.reactions)
        self.assertEqual(n_total, n1+n2)

        self.assertTrue("RHEA_66592_4_2_99_18" in net_merged.reactions)
        self.assertTrue("RHEA_64596_2_4_1_370" in net_merged.reactions)

        self.assertTrue("RHEA_66592_4_2_99_18" in net2.reactions)
        self.assertTrue("RHEA_64596_2_4_1_370" in net2.reactions)

        self.assertTrue("RHEA_66592_4_2_99_18" not in net1.reactions)
        self.assertTrue("RHEA_64596_2_4_1_370" not in net1.reactions)

        for k in net1.reactions:
            self.assertTrue(k in net_merged.reactions)
        for k in net2.reactions:
            self.assertTrue(k in net_merged.reactions)

        file_name = "merger"
        file_path = os.path.join(result_dir, file_name+"_net.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            f.write(net_merged.to_csv())

        file_path = os.path.join(result_dir, file_name+"_net.json")
        with open(file_path, 'w', encoding="utf-8") as f:
            json.dump(net_merged.dumps(), f)

        file_path = os.path.join(result_dir, file_name+"_stats.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            table = net_merged.get_compound_stats_as_table()
            f.write(table.to_csv())

        file_path = os.path.join(result_dir, file_name+"_gaps.csv")
        with open(file_path, 'w', encoding="utf-8") as f:
            table = net_merged.get_gaps_as_table()
            f.write(table.to_csv())
