import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, ScenarioProxy, Settings
from gws_gena import ContextImporter, DataProvider, FBAProto, NetworkImporter

settings = Settings.get_instance()


class TestFBA(BaseTestCaseUsingFullBiotaDB):
    def test_large_fba(self):
        data_dir = DataProvider.get_test_data_dir()

        def run_fba(organism, solver="highs", relax_qssa=False):
            experiment = ScenarioProxy(FBAProto)
            proto = experiment.get_protocol()
            organism_dir = os.path.join(data_dir, organism)
            # organism_result_dir = os.path.join(data_dir, "fba", organism)
            net = NetworkImporter.call(
                File(os.path.join(organism_dir, f"{organism}.json")), params={"add_biomass": True}
            )
            ctx = ContextImporter.call(
                File(path=os.path.join(organism_dir, f"{organism}_context_2simus.json"))
            )

            fba = proto.get_process("fba")

            proto.add_resource(
                instance_name="network_input",
                resource_model_id=str(net.id),
                in_port=fba << "network",
            )

            proto.add_resource(
                instance_name="context_input",
                resource_model_id=str(ctx.id),
                in_port=fba << "context",
            )

            fba.set_param("solver", solver)
            fba.set_param("relax_qssa", relax_qssa)
            fba.set_param("qssa_relaxation_strength", 1)
            if organism == "ecoli":
                fba.set_param("biomass_optimization", "maximize")
            else:
                fba.set_param("fluxes_to_maximize", ["pcys_Biomass:1.0"])

            experiment.run()

            # relax_dir = ""
            # if solver == "quad":
            #    relax_dir = "relax" if relax_qssa else "no-relax"

            # test results
            result = proto.get_output("fba_result")

            fluxes = result.get_fluxes_dataframe()
            self.print(fluxes)
            self.print(fluxes.abs().sum())
            sv = result.get_sv_dataframe()
            th, p = result.compute_zero_flux_threshold()
            self.print(
                f"sv_mean = {sv['value'].mean()}, sv_std = {sv['value'].std()}, sv_th={th}, sv_p = {p}"
            )

        # pcys
        for relax in [True]:
            organism = "pcys"
            self.print(f"Test FBAProto: Medium- or large-size network ({organism} + quad)")
            run_fba(organism=organism, solver="quad", relax_qssa=relax)
