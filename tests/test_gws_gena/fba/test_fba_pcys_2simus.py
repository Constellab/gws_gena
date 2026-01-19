import os

from gws_biota import BaseTestCaseUsingFullBiotaDB
from gws_core import File, InputTask, ResourceModel, ResourceOrigin, ScenarioProxy
from gws_gena import ContextImporter, DataProvider, FBAProto, NetworkImporter


class TestFBA(BaseTestCaseUsingFullBiotaDB):
    def test_large_fba(self):
        data_dir = DataProvider.get_test_data_dir()

        def run_fba(organism, solver="highs", relax_qssa=False):
            experiment = ScenarioProxy()
            proto = experiment.get_protocol()
            organism_dir = os.path.join(data_dir, organism)
            # organism_result_dir = os.path.join(data_dir, "fba", organism)
            net = NetworkImporter.call(
                File(os.path.join(organism_dir, f"{organism}.json")), params={"add_biomass": True}
            )
            ctx = ContextImporter.call(
                File(os.path.join(organism_dir, f"{organism}_context_2simus.json"))
            )
            fba_proto = proto.add_process(FBAProto, "fba_proto")

            net_resource_model: ResourceModel = ResourceModel.save_from_resource(
                net, origin=ResourceOrigin.UPLOADED
            )
            ctx_resource_model: ResourceModel = ResourceModel.save_from_resource(
                ctx, origin=ResourceOrigin.UPLOADED
            )

            context_resource = proto.add_process(
                InputTask, "context_resource", {InputTask.config_name: ctx_resource_model.id}
            )
            proto.add_connector(
                out_port=context_resource >> "resource", in_port=fba_proto << "context"
            )

            network_resource = proto.add_process(
                InputTask, "network_resource", {InputTask.config_name: net_resource_model.id}
            )
            proto.add_connector(
                out_port=network_resource >> "resource", in_port=fba_proto << "network"
            )
            fba_process = fba_proto.get_process("fba")
            fba_process.set_param("solver", solver)
            fba_process.set_param("relax_qssa", relax_qssa)
            fba_process.set_param("qssa_relaxation_strength", 1)

            fba_process.set_param("fluxes_to_maximize", ["pcys_Biomass:1.0"])

            experiment.run()

            # test results
            fba_proto.refresh()
            result = fba_proto.get_output("fba_result")

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
