import os

from gws_core import BaseTestCase, File, TableImporter, TaskRunner
from gws_gena import DataProvider
from gws_omix import IDConvertTask
from gws_gena.kegg.kegg_visualisation import KEGGVisualisation



class TestKEGGVisualisation(BaseTestCase):
    def test_kegg_visualisation(self):
        data_dir = DataProvider.get_test_data_dir()
        ## CASE HSA ONLY GENES ##
        self.print("Test KEGG Visualisation : human")
        # load genes:
        list_genes = File(os.path.join(data_dir, "kegg/genes_human.txt"))
        # create the taskrunner to call gprofiler to convert genes
        gprofiler = TaskRunner(
            task_type=IDConvertTask,
            inputs={"table_file": list_genes},
            params={"organism_name": 'Homo sapiens',
                    "id_column": "NCBI GeneID",
                    "target_namespace": "ENTREZGENE",
                    "numeric_namespace": "ENTREZGENE_ACC",
            }
        )
        gprofiler_output = gprofiler.run()
        annotated_table = gprofiler_output["annotated_file"]
        # create the TaskRunner
        runner_kegg_visualisation = TaskRunner(
            task_type=KEGGVisualisation,
            inputs={"deg_file": annotated_table},
            params={
                "organism_name": 'Homo sapiens',
                "id_column": "NCBI GeneID",
                "col_entrez": "converted",
                "min_genes_mapped_required": "0",
                "max_pathways_to_render": "1000"
                    }
                )
        # execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        # check if we retrieve the output
        pathways = outputs_kegg_visualisation["pathways"].get_resources()
        self.assertTrue("hsa00480.pathview.png" in pathways)
        list_pathway_error = outputs_kegg_visualisation["list_pathway_error"]
        self.assertTrue("hsa01240" in list_pathway_error.to_dataframe().values)

        ## CASE HSA ONLY GENES WITH TABLE ##
        self.print("Test KEGG Visualisation : human TABLE")
        # load genes:
        list_genes = TableImporter.call(
            File(path=os.path.join(data_dir, "kegg/genes_human.txt")), params={"index_column": -1}
        )
        # create the TaskRunner
        runner_kegg_visualisation = TaskRunner(
            task_type=KEGGVisualisation,
            inputs={"list_genes": list_genes},
            params={
                "genes_database": "entrez",
                "specie": "hsa",
                "email": "your email here",
                "fold_change": "No",
            },
        )
        # execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        # check if we retrieve the output
        pathways = outputs_kegg_visualisation["pathways"].get_resources()
        self.assertTrue("hsa00480.pathview.png" in pathways)
        list_pathway_error = outputs_kegg_visualisation["list_pathway_error"]
        self.assertTrue(
            "hsa01240" in list_pathway_error.to_dataframe().values
        )  ####################

        ## CASE HSA GENES + ONE FOLD CHANGE ##
        self.print("Test KEGG Visualisation : human + 1 fold change")
        # load genes:
        list_genes = File(os.path.join(data_dir, "kegg/genes_human_one_fold_change.txt"))
        # create the TaskRunner
        runner_kegg_visualisation = TaskRunner(
            task_type=KEGGVisualisation,
            inputs={"list_genes": list_genes},
            params={
                "genes_database": "entrez",
                "specie": "hsa",
                "email": "your email here",
                "fold_change": "Yes",
            },
        )
        # execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        # check if we retrieve the output
        pathways = outputs_kegg_visualisation["pathways"].get_resources()
        self.assertTrue("hsa00480.pathview.png" in pathways)
        list_pathway_error = outputs_kegg_visualisation["list_pathway_error"]
        self.assertTrue("hsa01240" in list_pathway_error.to_dataframe().values)

        ## CASE HSA GENES + TWO FOLD CHANGE ##
        self.print("Test KEGG Visualisation : human + 2 fold change")
        list_genes = File(os.path.join(data_dir, "kegg/genes_human_two_fold_change.txt"))
        # create the TaskRunner
        runner_kegg_visualisation = TaskRunner(
            task_type=KEGGVisualisation,
            inputs={"list_genes": list_genes},
            params={
                "genes_database": "entrez",
                "specie": "hsa",
                "email": "your email here",
                "fold_change": "Yes",
            },
        )
        # execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        # check if we retrieve the output
        pathways = outputs_kegg_visualisation["pathways"].get_resources()
        self.assertTrue("hsa00480.pathview.multi.png" in pathways)
        list_pathway_error = outputs_kegg_visualisation["list_pathway_error"]
        self.assertTrue("hsa01240" in list_pathway_error.to_dataframe().values)

        ## CASE HSA GENES ENSEMBL + TWO FOLD CHANGE ##
        self.print("Test KEGG Visualisation : human; genes ensembl + 2 fold change")
        list_genes = File(os.path.join(data_dir, "kegg/gene_Ensembl_human_with_two_fc.txt"))
        # create the TaskRunner
        runner_kegg_visualisation = TaskRunner(
            task_type=KEGGVisualisation,
            inputs={"list_genes": list_genes},
            params={
                "genes_database": "ensembl",
                "organism": "hsapiens",
                "specie": "hsa",
                "email": "your email here",
                "fold_change": "Yes",
            },
        )
        # execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        # check if we retrieve the output
        pathways = outputs_kegg_visualisation["pathways"].get_resources()
        self.assertTrue("hsa00562.pathview.multi.png" in pathways)
        list_pathway_error = outputs_kegg_visualisation["list_pathway_error"]
        self.assertTrue("hsa04215" in list_pathway_error.to_dataframe().values)
