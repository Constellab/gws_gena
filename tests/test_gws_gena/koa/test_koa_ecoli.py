import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings, TableImporter, TaskRunner
from gws_gena import (ContextImporter, KOAProto, NetworkImporter, TransformerEntityIDTable)

settings = Settings.get_instance()


class TestKOA(BaseTestCaseUsingFullBiotaDB):

    def test_ecoli_koa(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        experiment = IExperiment(KOAProto)
        proto = experiment.get_protocol()

        net = NetworkImporter.call(
            File(os.path.join(data_dir, "ecoli", "ecoli.json")),
            params = {"add_biomass" : True}
        )

        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "ecoli", "ecoli_context.json")),
            {}
        )
        ko_table = TableImporter.call(
            File(path=os.path.join(data_dir, "koa", "ecoli", "ko_table.csv")),
            {}
        )
        runner_transformer = TaskRunner( inputs={"table": ko_table},
            task_type=TransformerEntityIDTable, params = {'id_column_name': "id"})
        ko_table = runner_transformer.run()['transformed_table']

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

        self.assertAlmostEqual(table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 0.11665059205692323, delta=1e-1)

        table = ko_results.get_flux_dataframe(ko_id="ecoli_glu_L_c")
        self.assertAlmostEqual(table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 0.968142592801801, delta=1e-1)

    def test_ecoli_koa_genes(self):
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        experiment = IExperiment(KOAProto)
        proto = experiment.get_protocol()

        net = NetworkImporter.call(
            File(os.path.join(data_dir, "ecoli", "ecoli.json")),
            params = {"add_biomass" : True}
        )

        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "ecoli", "ecoli_context.json")),
            {}
        )
        ko_table = TableImporter.call(
            File(path=os.path.join(data_dir, "koa", "ecoli", "ko_table_genes.csv")),
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
        koa.set_param('type_ko',"genes")
        experiment.run()
        ko_results = proto.get_output("koa_result")

        table = ko_results.get_flux_dataframe(ko_id="ecoli_PGI")

        self.assertAlmostEqual(table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 0.9596382612800652, delta=1e-1)

        table = ko_results.get_flux_dataframe(ko_id='ecoli_PGI,ecoli_ACALDt,ecoli_CO2t,ecoli_O2t')
        self.assertAlmostEqual(table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 5.77666896310143e-05, delta=1e-1)
