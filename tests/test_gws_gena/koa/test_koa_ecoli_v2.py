import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings, TableImporter, TaskRunner
from gws_gena import (ContextImporter, TransformerEntityIDTable)
from gws_gena.proto.koa_proto_v2 import KOAProtoV2
from gws_gena.network.network_task.network_importer_v2 import NetworkImporterV2


settings = Settings.get_instance()


class TestKOA(BaseTestCaseUsingFullBiotaDB):

    def test_ecoli_koa(self):
        self.print("test ecoli")  # TODO : to delete
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        experiment = IExperiment(KOAProtoV2)
        proto = experiment.get_protocol()

        net = NetworkImporterV2.call(
            File(os.path.join(data_dir, "ecoli", "ecoli.json"))
        )

        ctx = ContextImporter.call(
            File(path=os.path.join(data_dir, "ecoli", "ecoli_context.json")),
            {}
        )
        ko_table = TableImporter.call(
            File(path=os.path.join(data_dir, "koa", "ecoli", "ko_table.csv")),
            {}
        )
        runner_transformer = TaskRunner(inputs={"table": ko_table},
                                        task_type=TransformerEntityIDTable, params={'id_column_name': "id"})
        ko_table = runner_transformer.run()['transformed_table']

        proto.set_input("network", net)
        proto.set_input("context", ctx)
        proto.set_input("ko_table", ko_table)

        koa = proto.get_process("koa")
        #koa.set_param("fluxes_to_maximize", ["e_coli_core_BIOMASS_Ecoli_core_w_GAM:1.0"])
        koa.set_param('biomass_optimization', "maximize")
        self.print("after fluxes")  # TODO : to delete
        koa.set_param("solver", "quad")
        koa.set_param("relax_qssa", True)
        koa.set_param('qssa_relaxation_strength', 1)
        koa.set_param("add_biomass", True)
        experiment.run()
        ko_results = proto.get_output("koa_result")

        table = ko_results.get_flux_dataframe(ko_id="e_coli_core_PFK")
        self.print("test run pfk !! ")  # TODO : to delete
        network = net
        model = network.get_cobra_model()
        with model:
            model.reactions.PFK.knock_out()
            self.print(f'pfk knocked out: {model.optimize()}' )
        self.print(f"value {table.at['e_coli_core_BIOMASS_Ecoli_core_w_GAM', 'value']}  !!!" )
        self.assertAlmostEqual(table.at["e_coli_core_BIOMASS_Ecoli_core_w_GAM", "value"],
                               0.704, delta=1e-1)


        table = ko_results.get_flux_dataframe(ko_id="e_coli_core_PGK")
        self.print("test run")  # TODO : to delete

        self.assertAlmostEqual(table.at["e_coli_core_BIOMASS_Ecoli_core_w_GAM", "value"],
                               0.11665059205692323, delta=1e-1)  # TODO: le test ne passe pas !!

        table = ko_results.get_flux_dataframe(ko_id="e_coli_core_glu_L_c")
        self.assertAlmostEqual(
            table.at["e_coli_core_BIOMASS_Ecoli_core_w_GAM", "value"], 0.968142592801801, delta=1e-1)

    def test_ecoli_koa_genes(self):
        self.print("test ecoli genes")  # TODO : to delete
        data_dir = settings.get_variable("gws_gena:testdata_dir")
        experiment = IExperiment(KOAProtoV2)
        proto = experiment.get_protocol()

        net = NetworkImporterV2.call(
            File(os.path.join(data_dir, "ecoli", "ecoli.json"))
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
        koa.set_param('biomass_optimization', "maximize")
        #koa.set_param('fluxes_to_maximize', "e_coli_core_BIOMASS_Ecoli_core_w_GAM:1.0") #TODO
        koa.set_param("solver", "quad")
        koa.set_param("relax_qssa", True)
        koa.set_param('qssa_relaxation_strength', 1)
        koa.set_param('type_ko', "genes")
        koa.set_param("add_biomass", True)
        experiment.run()
        ko_results = proto.get_output("koa_result")

        self.print(ko_results)  # TODO to delete
        self.print(ko_results.get_ko_ids())  # TODO to delete
        table = ko_results.get_flux_dataframe(ko_id="ecoli_PGI")

        self.assertAlmostEqual(
            table.at["e_coli_core_BIOMASS_Ecoli_core_w_GAM", "value"], 0.9596382612800652, delta=1e-1)

        table = ko_results.get_flux_dataframe(
            ko_id='ecoli_PGI,ecoli_ACALDt,ecoli_CO2t,ecoli_O2t')
        self.assertAlmostEqual(table.at["e_coli_core_BIOMASS_Ecoli_core_w_GAM", "value"],
                               5.77666896310143e-05, delta=1e-1)  # TODO: le test ne passe pas !!
