from gws_gena.kegg.kegg_visualisation import KEGGVisualisation
from gws_core import (File,TaskRunner,Table,TableImporter)
from gws_core import BaseTestCase


class TestKEGGVisualisation(BaseTestCase):
    def test_kegg_visualisation(self):
        ## CASE HSA ONLY GENES ##
        self.print(f"Test KEGG Visualisation : human")
        #load genes:
        list_genes= File("/lab/user/bricks/gws_gena/tests/testdata/kegg/genes_human.txt")
        #create the TaskRunner
        runner_kegg_visualisation = TaskRunner(task_type=KEGGVisualisation,
                                inputs={'list_genes':  list_genes},
                                params = {'genes_database': "entrez",
                                        'specie': "hsa",
                                        'email': "your email here",
                                        'fold_change': "No"})
        #execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        #check if we retrieve one of the output
        pathways = outputs_kegg_visualisation['pathways'].get_resources()
        self.assertTrue("hsa00480.pathview.png" in pathways)

        ## CASE HSA GENES + ONE FOLD CHANGE ##
        self.print(f"Test KEGG Visualisation : human + 1 fold change")
        #load genes:
        list_genes= File("/lab/user/bricks/gws_gena/tests/testdata/kegg/genes_human_one_fold_change.txt")
        #create the TaskRunner
        runner_kegg_visualisation = TaskRunner(task_type=KEGGVisualisation,
                                inputs={'list_genes':  list_genes},
                                params = {'genes_database': "entrez",
                                        'specie': "hsa",
                                        'email': "your email here",
                                        'fold_change': "Yes"})
        #execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        #check if we retrieve one of the output
        pathways = outputs_kegg_visualisation['pathways'].get_resources()
        self.assertTrue("hsa00480.pathview.png" in pathways)

        ## CASE HSA GENES + TWO FOLD CHANGE ##
        self.print(f"Test KEGG Visualisation : human + 2 fold change")
        list_genes= File("/lab/user/bricks/gws_gena/tests/testdata/kegg/genes_human_two_fold_change.txt")
        #create the TaskRunner
        runner_kegg_visualisation = TaskRunner(task_type=KEGGVisualisation,
                                inputs={'list_genes':  list_genes},
                                params = {'genes_database': "entrez",
                                        'specie': "hsa",
                                        'email': "your email here",
                                        'fold_change': "Yes"})
        #execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        #check if we retrieve one of the output
        pathways = outputs_kegg_visualisation['pathways'].get_resources()
        self.assertTrue("hsa00480.pathview.multi.png" in pathways)


        ## CASE HSA GENES ENSEMBL + TWO FOLD CHANGE ##
        self.print(f"Test KEGG Visualisation : human; genes ensembl + 2 fold change")
        list_genes= File("/lab/user/bricks/gws_gena/tests/testdata/kegg/gene_Ensembl_human_with_two_fc.txt")
        #create the TaskRunner
        runner_kegg_visualisation = TaskRunner(task_type=KEGGVisualisation,
                                inputs={'list_genes':  list_genes},
                                params = {'genes_database': "ensembl",
                                        'organism':'hsapiens',
                                        'specie': "hsa",
                                        'email': "your email here",
                                        'fold_change': "Yes"})
        #execute the TaskRunner
        outputs_kegg_visualisation = runner_kegg_visualisation.run()

        #check if we retrieve one of the output
        pathways = outputs_kegg_visualisation['pathways'].get_resources()
        self.assertTrue("hsa00562.pathview.multi.png" in pathways)
