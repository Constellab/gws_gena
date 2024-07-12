
import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, IExperiment, Settings
from gws_gena import ContextImporter
from gws_gena.network_v2.network_importer_v2 import NetworkImporterV2
from gws_gena.proto.fva_proto_v2 import FVAProtoV2

settings = Settings.get_instance()


class TestFVA(BaseTestCaseUsingFullBiotaDB):

    def test_large_pcys(self):
        self.print("Test FBAProto: Medium or large metwork (typically Ecoli)")
        data_dir = settings.get_variable("gws_gena:testdata_dir")

        def run_fva(organism, solver="highs", relax_qssa=False):
            experiment = IExperiment(FVAProtoV2)
            proto = experiment.get_protocol()
            organism_dir = os.path.join(data_dir, organism)
            organism_result_dir = os.path.join(data_dir, 'fva', organism)
            net = NetworkImporterV2.call(
                File(path=os.path.join(organism_dir, f"{organism}_v2.json")), params={"biomass_metabolite_id_user": "Biomass_b"}#TODO: avant on ajoutait un composé ...
            )
            ctx = ContextImporter.call(File(
                path=os.path.join(organism_dir, f"{organism}_context.json")
            ))

            proto.set_input("network", net)
            proto.set_input("context", ctx)
            fva = proto.get_process("fva")
            fva.set_param('solver', solver)
            fva.set_param('relax_qssa', relax_qssa)
            fva.set_param('qssa_relaxation_strength', 1)
            if organism == 'ecoli':
                fva.set_param('fluxes_to_maximize', [
                              "ecoli_BIOMASS_Ecoli_core_w_GAM:1.0"])
            else:
                fva.set_param('fluxes_to_maximize', ["Biomass:1.0"])

            experiment.run()

            relax_dir = ""
            if solver == "quad":
                relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fva_result")
            # biomass_flux = result.get_biomass_flux_dataframe()
            # print("---------------- BIOMASS FLUX ----------------")
            # print(biomass_flux)
            # print("----------------------------------------------")

            # result_dir = os.path.join(organism_result_dir, solver, relax_dir)
            # file_path = os.path.join(result_dir, "biomass_flux.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #    fp.write(biomass_flux.to_csv())

            sv = result.get_sv_dataframe()
            th, p = result.compute_zero_flux_threshold()
            print(
                f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}")

            # if not os.path.exists(result_dir):
            #     os.makedirs(result_dir)
            # file_path = os.path.join(result_dir, "flux.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(fluxes.to_csv())
            # file_path = os.path.join(result_dir, "sv.csv")
            # with open(file_path, 'w', encoding="utf-8") as fp:
            #     fp.write(sv.to_csv())
            # table = fluxes.to_numpy()
            # table = numpy.array(table, dtype=float)
            # file_path = os.path.join(result_dir, "flux.csv")
            # expected_table = pandas.read_csv(file_path, index_col=0, header=0)
            # expected_table = expected_table.to_numpy()
            # expected_table = numpy.array(expected_table, dtype=float)
            # self.assertTrue(numpy.isclose(table, expected_table, rtol=1e-1).all())

        # pcys
        organism = "pcys"
        run_fva(organism=organism, solver="quad", relax_qssa=True)
