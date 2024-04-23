import os
import sys

import pandas as pd
from bioservices.kegg import KEGG
from Bio import Entrez
from gws_core import (File,Table,ResourceSet,OutputSpec, OutputSpecs, InputSpec, InputSpecs,task_decorator,TaskInputs,Task,
                    StrParam, TaskOutputs,ConfigParams,ShellProxy, TableImporter, TypingStyle)
from .kegg_r_env_task import KeggREnvHelper


@task_decorator("KEGGVisualisation", human_name="Kegg Visualisation",
                short_description="Generate KEGG pathway from a list of genes.",
                style=TypingStyle.material_icon(material_icon_name="collections_bookmark", background_color="#d9d9d9"))
class KEGGVisualisation(Task):
    """
    Generates a KEGG pathway using the genes specified in the input.

    Please provide a list of genes such as:
    ,FoldChange
    Gene1,value
    Gene2,value

    If you don't have gene expression, just provide the gene names with a header.
    If you want to compare more than one fold change, add the other fold change in the following columns.
    In the output, each box of the pathway will be separated depending on the number of fold changes.
    So the colours may be different depending on the condition.

    For the specie, you need to provide the kegg.code. You can find the list of allowed values attached to this story: https://constellab.community/stories/e330483b-5b9e-452c-b5a4-f6b62506c9ad/how-to-visualise-a-kegg-pathway-using-constellab#introduction

    Organism names are constructed by concatenating the first letter of the name and the family name. Example: human - 'hsapiens', mouse - 'mmusculus'.
    You can find the complete list here: https://biit.cs.ut.ee/gprofiler/page/organism-list

    Be aware that this task can take some time, especially the first time, as a virtual environment has to be installed, and also depending on the length of the genes provided, it can take more time.

    In the output you will also get a Table with the pathways where genes are mapped, but these pathways can't be shown with the pathview package.

    KEGG is a database resource for understanding high-level functions and utilities of the biological system.
    Kanehisa Laboratories owns and controls the rights to KEGG.
    Although the KEGG database is made freely available for academic use via the website, it is not in the public domain.
    All commercial use of KEGG requires a license. Please ensure that you have licence to use KEGG database.
    """

    input_specs = InputSpecs({
        'list_genes': InputSpec([File,Table], human_name="Genes List ", short_description="The file or the Table with genes and fold changes."),
    })
    output_specs = OutputSpecs({
        'pathways': OutputSpec(ResourceSet, human_name='Pathways KEGG', short_description='Pathways KEGG colored.'),
        'list_pathway_error': OutputSpec(Table, human_name='list_pathway_error', short_description='List of pathways in error.')
    })
    config_specs = {
            'genes_database': StrParam(
            default_value="entrez", allowed_values=["entrez","ensembl"],
            human_name="Genes Database", short_description="The database of the genes."),
            'organism': StrParam(
            human_name="Organism", optional = True, short_description="If genes are ensembl genes, please provide the organism studied (see documentation)"),
            'specie': StrParam(
            human_name="Specie", short_description="The specie studied."),
            'email': StrParam(
            default_value = "your email here", human_name="Email", short_description="Your email to use NCBI."),
            "fold_change": StrParam(
            default_value="No", allowed_values=["No","Yes"],
            human_name="Fold Change", short_description="Does the file contain the fold change of gene expression?")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        if isinstance(inputs['list_genes'],Table):
            list_genes: Table = inputs['list_genes']
            list_genes = list_genes.to_dataframe()
            list_genes_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "list_genes.csv")
            list_genes.to_csv(list_genes_path, index=False)
            list_genes = File(list_genes_path)

        elif isinstance(inputs['list_genes'],File):
            list_genes: File = inputs['list_genes']

        genes_database = params['genes_database']
        fold_change = params['fold_change']
        specie = params['specie']

        #Test if the specie provided is in the list of allowed organisms:
        allowed_organisms = pd.read_csv(os.path.join(
            os.path.abspath(os.path.dirname(__file__)), "list_organisms_pathview.txt"), header=0, index_col=0)
        if specie not in allowed_organisms["kegg.code"].values:
            raise Exception("The specie provided doesn't correspond to a kegg.code allowed. You can find the list of allowed values attached to this story: https://constellab.community/stories/e330483b-5b9e-452c-b5a4-f6b62506c9ad/how-to-visualise-a-kegg-pathway-using-constellab#introduction")


        ## Search all pathways where genes are evolved ##
        if genes_database == "ensembl":
            organism = params['organism']
            #Run script R to translate gene ensembl to entrez genes names
            path_script_translate_ensembl_to_entrez = os.path.join(os.path.abspath(os.path.dirname(__file__)), "translate_ensembl_to_entrez.R")

            cmd = f"Rscript --vanilla {path_script_translate_ensembl_to_entrez} {list_genes.path} {organism}"

            shell_proxy: ShellProxy = KeggREnvHelper.create_proxy(self.message_dispatcher)
            self.log_info_message('Translate gene ensembl to entrez genes names')
            result = shell_proxy.run(cmd, shell_mode=True)

            if result != 0:
                raise Exception("An error occured during the execution of the script to translate ensembl genes into entrez genes.")

            # Loop through the working directory and retrieve the list converted
            self.log_info_message('Retrieve list of genes translated')
            for filename in os.listdir(shell_proxy.working_dir):
                file_path = os.path.join(shell_proxy.working_dir, filename)
                if os.path.isfile(file_path):
                    if filename.endswith("gene_entrez.csv"):
                        list_genes = File(file_path)


        data = pd.read_csv(list_genes.path, header=0, index_col=0)
        #transform int data into str data
        list_gene_entrez = list(map(str, data.index))



        #We search the KEGG pathway in which the genes are evolved and we create a list of these pathways
        self.log_info_message('Search the KEGG pathway in which the genes are evolved. This step can be long if there are many genes.')
        k = KEGG()
        list_code_pathways = []
        for gene in list_gene_entrez :
            pathways = k.get_pathway_by_gene(gene=gene, organism = specie)
            if pathways is not None:
                for code_pathway in pathways :
                    list_code_pathways.append(code_pathway)
        #We keep only unique pathway
        pathway_kegg = list(set(list_code_pathways))

        if not pathway_kegg :
            # *Always* tell NCBI who you are
            Entrez.email = params['email']

            #We use the function to convert gene id to gene names
            ret = self.retrieve_annotation(list_gene_entrez)

            #We create a list with the names
            name = []
            for i in range (0, len(ret["DocumentSummarySet"]["DocumentSummary"])):
                name.append(ret["DocumentSummarySet"]["DocumentSummary"][i]["Name"])

            #We search the KEGG pathway in which the genes are evolved and we create a list of these pathways
            self.log_info_message('Search the KEGG pathway in which the genes are evolved. This step can be long if there are many genes.')
            k = KEGG()
            list_code_pathways = []
            for gene in name :
                pathways = k.get_pathway_by_gene(gene=gene, organism = specie)
                if pathways is not None:
                    for code_pathway in pathways :
                        list_code_pathways.append(code_pathway)
            #We keep only unique pathway
            pathway_kegg = list(set(list_code_pathways))
            if not pathway_kegg :
                raise Exception("No mapped pathway was found for the genes provided. Check or improve your list.")

        #We save these pathways in a file
        pathway_kegg_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "pathway_kegg.csv")

        with open(pathway_kegg_path, "w") as opfile:
            opfile.write("\n".join(pathway_kegg))
        pathway_kegg = File(pathway_kegg_path)

        ## Map genes on pathways ##
        # Using the R script
        path_script_kegg_visu = os.path.join(os.path.abspath(os.path.dirname(__file__)), "kegg_visualisation.R")
        cmd = f"Rscript --vanilla {path_script_kegg_visu} {list_genes.path} {specie} {pathway_kegg.path} {fold_change}"

        shell_proxy: ShellProxy = KeggREnvHelper.create_proxy(self.message_dispatcher)
        self.log_info_message('Mapping genes on KEGG pathways')
        result = shell_proxy.run(cmd, shell_mode=True)

        if result != 0:
            raise Exception("An error occured during the execution of the script using pathview.")

        # Loop through the working directory and add files to the resource set
        self.log_info_message('Prepare output')

        #retrieve the list of pathways with error
        list_pathway_error = os.path.join(shell_proxy.working_dir, "list_pathway_error.csv")
        list_pathway_error = TableImporter.call(File(path=list_pathway_error), params={"index_column": -1})
        dataframe_pathway_error = list_pathway_error.to_dataframe()

        resource_set_pathways: ResourceSet = ResourceSet()
        resource_set_pathways.name = "Set of pathways"
        for filename in os.listdir(shell_proxy.working_dir):
            file_path = os.path.join(shell_proxy.working_dir, filename)
            if os.path.isfile(file_path):
                if filename.endswith("pathview.png") or filename.endswith("pathview.multi.png"):
                    if filename.split(".pathview")[0] not in dataframe_pathway_error.values :
                        resource_set_pathways.add_resource(File(file_path), filename)


        return {'pathways': resource_set_pathways, 'list_pathway_error': list_pathway_error}

    #Function to convert gene id to gene names
    def retrieve_annotation(self,id_list):
        request = Entrez.epost("gene", id=",".join(id_list))
        try:
            result = Entrez.read(request)
        except RuntimeError as e:
            sys.exit(-1)
        web_env = result["WebEnv"]
        query_key = result["QueryKey"]
        data = Entrez.esummary(db="gene", webenv=web_env, query_key=query_key)
        annotations = Entrez.read(data)
        return annotations
