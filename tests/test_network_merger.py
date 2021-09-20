
import os, json

from gws_core import Settings, Protocol, IExperiment, Experiment, File, ProcessSpec, ConfigParams, protocol_decorator
from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_gena import NetworkMerger, Twin, TwinContext, NetworkLoader

settings = Settings.retrieve()

@protocol_decorator("MergerProtocol")
class MergerProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        
        loader_1: ProcessSpec = self.add_process(NetworkLoader, 'loader_1')
        loader_1.set_param("file_path", os.path.join(data_dir, "recon", "recon_net.json"))

        loader_2: ProcessSpec = self.add_process(NetworkLoader, 'loader_2')
        loader_2.set_param("file_path", os.path.join(data_dir, "network_merger", "addon.json"))
        merger: ProcessSpec = self.add_process(NetworkMerger, 'merger')

        self.add_connectors([
            (loader_1>>"data", merger<<"network_1"),
            (loader_2>>"data", merger<<"network_2")
        ])

class TestMerge(BaseTestCaseUsingFullBiotaDB):
    
    async def test_merger(self):
        self.print("Test Merger")

        experiment = IExperiment(MergerProtocol)
        proto = experiment.get_protocol()
        merger = proto.get_process("merger")

        data_dir = settings.get_variable("gws_gena:testdata_dir")
        result_dir = os.path.join(data_dir, "network_merger")
        async def assert_results(net, file_name):
            # file_path = os.path.join(result_dir, file_name+"_net.csv")
            # with open(file_path, 'w') as f:
            #    f.write(net.to_csv())

            # file_path = os.path.join(result_dir, file_name+"_net.json")
            # with open(file_path, 'w') as f:
            #     json.dump(net.to_json(), f)

            file_path = os.path.join(result_dir, file_name+"_net.csv")
            with open(file_path, 'r') as f:
                self.assertEqual(net.to_csv(), f.read())

            file_path = os.path.join(result_dir, file_name+"_stats.csv")
            with open(file_path, 'w') as f:
                table = net.render__compound_stats__as_table()
                f.write(table.to_csv())
            
            file_path = os.path.join(result_dir, file_name+"_gaps.csv")
            with open(file_path, 'w') as f:
                table = net.render__gaps__as_table()
                f.write(table.to_csv())

        await experiment.run()
        net = merger.get_output("network")
        file_name = "merger"
        await assert_results(net, file_name)