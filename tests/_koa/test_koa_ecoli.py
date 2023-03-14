import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings
from gws_gena import (ContextImporter, EntityIDTableImporter, KOAProto,
                      NetworkImporter)

settings = Settings.get_instance()


class TestKOA(BaseTestCaseUsingFullBiotaDB):

    def test_ecoli_koa(self):
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
        koa.set_param("fluxes_to_maximize", ["ecoli_BIOMASS_Ecoli_core_w_GAM"])
        koa.set_param("solver", "quad")
        koa.set_param("relax_qssa", True)
        koa.set_param('qssa_relaxation_strength', 1)
        experiment.run()
        ko_results = proto.get_output("koa_result")

        print(ko_results)

        table = ko_results.get_flux_dataframe(ko_id="ecoli_PGK")

        print(table)

        self.assertAlmostEqual(table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 37.15, delta=1e-2)

        table = ko_results.get_flux_dataframe(ko_id="ecoli_glu_L_c")
        self.assertAlmostEqual(table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 51.27, delta=1e-2)
