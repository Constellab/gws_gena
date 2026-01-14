from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, ScenarioProxy, Settings, TableImporter, TaskRunner
from gws_gena import (
    ContextImporter,
    DataProvider,
    KOAProto,
    NetworkImporter,
    TransformerEntityIDTable,
)

settings = Settings.get_instance()


class TestKOA(BaseTestCaseUsingFullBiotaDB):
    def test_ecoli_koa(self):
        experiment = ScenarioProxy(KOAProto)
        proto = experiment.get_protocol()

        net = NetworkImporter.call(
            File(DataProvider.get_test_data_path("ecoli/ecoli.json")), params={"add_biomass": True}
        )

        ctx = ContextImporter.call(
            File(path=DataProvider.get_test_data_path("ecoli/ecoli_context.json")), {}
        )
        ko_table = TableImporter.call(
            File(path=DataProvider.get_test_data_path("koa/ecoli/ko_table.csv")), {}
        )
        runner_transformer = TaskRunner(
            inputs={"table": ko_table},
            task_type=TransformerEntityIDTable,
            params={"id_column_name": "id"},
        )
        ko_table = runner_transformer.run()["transformed_table"]

        koa = proto.get_process("koa")

        proto.add_resource(
            instance_name="network_input",
            resource_model_id=str(net.id),
            in_port=koa << "network",
        )

        proto.add_resource(
            instance_name="context_input",
            resource_model_id=str(ctx.id),
            in_port=koa << "context",
        )

        proto.add_resource(
            instance_name="ko_table_input",
            resource_model_id=str(ko_table.id),
            in_port=koa << "ko_table",
        )

        koa.set_param("fluxes_to_maximize", ["ecoli_BIOMASS_Ecoli_core_w_GAM"])
        koa.set_param("solver", "quad")
        koa.set_param("relax_qssa", True)
        koa.set_param("qssa_relaxation_strength", 1)
        experiment.run()
        ko_results = proto.get_output("koa_result")

        self.print(str(ko_results))

        table = ko_results.get_flux_dataframe(ko_id="ecoli_PGK")

        self.print(table)
        self.assertAlmostEqual(
            table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 0.11665059205692323, delta=1e-1
        )

        table = ko_results.get_flux_dataframe(ko_id="ecoli_glu_L_c")
        self.assertAlmostEqual(
            table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 0.968142592801801, delta=1e-1
        )

    def test_ecoli_koa_genes(self):
        experiment = ScenarioProxy(KOAProto)
        proto = experiment.get_protocol()

        net = NetworkImporter.call(
            File(DataProvider.get_test_data_path("ecoli/ecoli.json")), params={"add_biomass": True}
        )

        ctx = ContextImporter.call(
            File(path=DataProvider.get_test_data_path("ecoli/ecoli_context.json")), {}
        )
        ko_table = TableImporter.call(
            File(path=DataProvider.get_test_data_path("koa/ecoli/ko_table_genes.csv")), {}
        )

        koa = proto.get_process("koa")

        proto.add_resource(
            instance_name="network_input",
            resource_model_id=str(net.id),
            in_port=koa << "network",
        )

        proto.add_resource(
            instance_name="context_input",
            resource_model_id=str(ctx.id),
            in_port=koa << "context",
        )

        proto.add_resource(
            instance_name="ko_table_input",
            resource_model_id=str(ko_table.id),
            in_port=koa << "ko_table",
        )

        koa.set_param("fluxes_to_maximize", ["ecoli_BIOMASS_Ecoli_core_w_GAM"])
        koa.set_param("solver", "quad")
        koa.set_param("relax_qssa", True)
        koa.set_param("qssa_relaxation_strength", 1)
        koa.set_param("type_ko", "genes")
        experiment.run()
        ko_results = proto.get_output("koa_result")

        table = ko_results.get_flux_dataframe(ko_id="ecoli_PGI")

        self.assertAlmostEqual(
            table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 0.9596382612800652, delta=1e-1
        )

        table = ko_results.get_flux_dataframe(ko_id="ecoli_PGI,ecoli_ACALDt,ecoli_CO2t,ecoli_O2t")
        self.assertAlmostEqual(
            table.at["ecoli_BIOMASS_Ecoli_core_w_GAM", "value"], 5.77666896310143e-05, delta=1e-1
        )
