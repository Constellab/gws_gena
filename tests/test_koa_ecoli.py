import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import (ConfigParams, File, IExperiment, Settings, TaskRunner,
                      ViewTester)
from gws_gena import (KOA, Context, ContextImporter, EntityIDTable,
                      EntityIDTableImporter, KOAProto, Network,
                      NetworkImporter, Twin)

settings = Settings.retrieve()


class TestKOA(BaseTestCaseUsingFullBiotaDB):

    async def test_ecoli_koa(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        experiment = IExperiment(KOAProto)
        proto = experiment.get_protocol()

        net = NetworkImporter.call(
            File(os.path.join(data_dir, "ecoli", "ecoli.json")),
            {}
        )
        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "ecoli", "ecoli_context.json")),
            {}
        )
        ko_table = EntityIDTableImporter.call(
            File(path=os.path.join(data_dir, "koa", "ecoli", "ko_table.csv")),
            {}
        )

        proto.set_input("network", net)
        proto.set_input("context", ctx)
        proto.set_input("ko_table", ko_table)

        koa = proto.get_process("koa")
        koa.set_param("monitored_fluxes", ["ecoli_BIOMASS_Ecoli_core_w_GAM"])
        koa.set_param("fluxes_to_maximize", ["ecoli_BIOMASS_Ecoli_core_w_GAM"])
        koa.set_param("solver", "quad")
        koa.set_param("relax_qssa", True)
        await experiment.run()
        ko_results = proto.get_output("ko_result")

        print(ko_results)

        self.assertAlmostEqual(ko_results.get_flux_dataframe().at[0, "flux_value"], 37.137627, delta=1e-6)
        self.assertAlmostEqual(ko_results.get_flux_dataframe().at[1, "flux_value"], 51.262072, delta=1e-6)
