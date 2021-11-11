
import json
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, Experiment, File, IExperiment, ProcessSpec,
                      Protocol, Settings, protocol_decorator)
from gws_gena import NetworkImporter, NetworkMerger, Twin, TwinContext

settings = Settings.retrieve()


@protocol_decorator("MergerProtocol")
class MergerProtocol(Protocol):
    def configure_protocol(self, _: ConfigParams) -> None:
        loader_1: ProcessSpec = self.add_process(NetworkImporter, 'loader_1')
        loader_2: ProcessSpec = self.add_process(NetworkImporter, 'loader_2')
        merger: ProcessSpec = self.add_process(NetworkMerger, 'merger')

        self.add_connectors([
            (loader_1 >> "resource", merger << "network_1"),
            (loader_2 >> "resource", merger << "network_2")
        ])

        self.add_interface('file1', loader_1, 'file')
        self.add_interface('file2', loader_2, 'file')


class TestMerge(BaseTestCaseUsingFullBiotaDB):

    async def test_merger(self):
        self.print("Test Merger")

        experiment = IExperiment(MergerProtocol)
        proto = experiment.get_protocol()
        merger = proto.get_process("merger")

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        proto.set_input('file1', File(path=os.path.join(data_dir, "recon", "recon_net.json")))
        proto.set_input('file2', File(path=os.path.join(data_dir, "network_merger", "addon.json")))

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        result_dir = os.path.join(data_dir, "network_merger")

        async def assert_results(net, file_name):
            # file_path = os.path.join(result_dir, file_name+"_net.csv")
            # with open(file_path, 'w') as f:
            #    f.write(net.to_csv())

            # file_path = os.path.join(result_dir, file_name+"_net.json")
            # with open(file_path, 'w') as f:
            #     json.dump(net.dumps(), f)

            file_path = os.path.join(result_dir, file_name+"_net.csv")
            with open(file_path, 'r') as f:
                self.assertEqual(net.to_csv(), f.read())

            file_path = os.path.join(result_dir, file_name+"_stats.csv")
            with open(file_path, 'w') as f:
                table = net.get_compound_stats_as_table()
                f.write(table.to_csv())

            file_path = os.path.join(result_dir, file_name+"_gaps.csv")
            with open(file_path, 'w') as f:
                table = net.get_gaps_as_table()
                f.write(table.to_csv())

        await experiment.run()

        net = merger.get_output("network")
        file_name = "merger"

        await assert_results(net, file_name)
