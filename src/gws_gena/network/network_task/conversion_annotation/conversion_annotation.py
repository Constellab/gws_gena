import pandas as pd
from cobra.io import load_json_model, save_json_model

from gws_core import (ConfigParams, InputSpec, OutputSpec, File,
                      Task, TaskInputs, TaskOutputs, task_decorator, StrParam,Table)


@task_decorator("ConvertAnnotation", human_name="Convert Model Annotation",
                short_description="This task adds metabolites and reactions identifiers (ChEBI, Rhea and ec-number) to a model")
class ConvertAnnotation(Task):
    """
    Convert annotation task class

    Complete the annotation of a metabolic model thanks to internal correspondence tables.
    This task can add missing identifiers to metabolics and reactions. For metabolites, it adds ChEBI identifiers. For reactions, it can add Rhea identifiers and EC numbers.  
    """
    input_specs = {'input_model':  InputSpec(File, human_name="Model", short_description="The model to annotate")}
    output_specs = {
    'output_model_annotated': OutputSpec(File, human_name="Model annotated", short_description="The model completed"),
    'output_results': OutputSpec(Table, human_name="Results Annotation", short_description="The annotation result table")}
    config_specs = {
        "metabolites_id":
        StrParam(
            allowed_values=["", "BiGG", "Literal name", "Other"],
            default_value=None, optional=False, human_name="Metabolite ID",
            short_description="What is the type of metabolite 'id'?"),
        "metabolites_name":
        StrParam(
            allowed_values=["", "BiGG", "Literal name", "Other"],
            default_value=None, optional=False, human_name="Metabolite name",
            short_description="What is the type of metabolite 'name'?"),
        "reaction_id":
        StrParam(
            allowed_values=["", "BiGG", "Other"],
            default_value=None, optional=False, human_name="Reaction ID",
            short_description="What is the type of reaction 'id'?"),
        "reaction_name":
        StrParam(
            allowed_values=["", "BiGG", "Other"],
            default_value=None, optional=False, human_name="Reaction name",
            short_description="What is the type of reaction 'name'?")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        input_model: File = inputs['input_model']
        #Load metabolic model
        model = load_json_model(input_model)
        #Load the database Reactions
        db_bigg_rhea=pd.read_csv("/lab/user/bricks/gws_gena/src/gws_gena/network/network_task/conversion_annotation/database_bigg_rhea.csv",sep='\t')
        #Load the database Metabolites
        db_bigg_chebi=pd.read_csv("/lab/user/bricks/gws_gena/src/gws_gena/network/network_task/conversion_annotation/database_bigg_chebi.csv",sep='\t')

        metabolites_id = params["metabolites_id"]
        metabolites_name = params["metabolites_name"]
        reaction_id = params["reaction_id"]
        reaction_name = params["reaction_name"]


        #### Metabolites
        index_metabolite = 0
        chebi_filled_db = 0
        if(metabolites_id != "Other" or metabolites_name!= "Other"):
            model,index_metabolite,chebi_filled_db = self.annotate_metabolites(model, db_bigg_chebi,metabolites_id, metabolites_name)

        #### Reactions
        index_reactions = 0
        rhea_filled_db = 0
        ecnumber_filled_db = 0
        if(reaction_id != "Other" or reaction_name!= "Other"):
            model, index_reactions,rhea_filled_db,ecnumber_filled_db = self.annotate_reactions(model, db_bigg_rhea,reaction_id,reaction_name)

        columns_results = ("Number reactions","Rhea filled","EC number filled","Number metabolites","ChEBI filled")
        results = pd.DataFrame(columns=columns_results)
        row = pd.DataFrame([[index_reactions, rhea_filled_db,ecnumber_filled_db, index_metabolite, chebi_filled_db]], columns=columns_results)
        results= pd.concat([results, row])

        # Output
        save_json_model(model, "model_annotated.json")
        model_annotated = File("model_annotated.json")
        #results.to_csv("results.csv", index=False)
        #results = File("results.csv")
        results_table = Table(results)

        return {'output_model_annotated': model_annotated,
        'output_results' : results_table}

    def annotate_metabolites(self,model,db_bigg_chebi,metabolites_id, metabolites_name):
        index_metabolite = 0
        chebi_filled_db = 0

        for metabolite in model.metabolites:
            #We give priority if there are BiGG identifiers
            if(metabolites_name == "BiGG" or metabolites_id == "BiGG"):
                if (metabolites_name == "BiGG"):
                    bigg = metabolite.name
                elif(metabolites_id == "BiGG"):
                    bigg = metabolite.id
                #We search into the database we created
                if (bigg in db_bigg_chebi.BIGG.values):
                    index_bigg = db_bigg_chebi.index[(db_bigg_chebi['BIGG'] == bigg)].tolist()[0]
                    try:
                        chebi = metabolite.annotation["chebi"]
                    except :
                        id_chebi= db_bigg_chebi["CHEBI"][index_bigg]
                        metabolite.annotation["chebi"] = str(id_chebi)
                        chebi_filled_db +=1

                index_metabolite += 1

            elif (metabolites_name == "Literal name" or metabolites_id == "Literal name"):
                if (metabolites_name == "Literal name"):
                    name = metabolite.name.lower()
                elif(metabolites_id == "Literal name"):
                    name = metabolite.id.lower()
                #We search into the database we created
                if (name in db_bigg_chebi.Name.values):
                    index_bigg = db_bigg_chebi.index[(db_bigg_chebi['Name'] == name)].tolist()[0]
                    try:
                        chebi = metabolite.annotation["chebi"]
                    except :
                        id_chebi= db_bigg_chebi["CHEBI"][index_bigg]
                        metabolite.annotation["chebi"] = str(id_chebi)
                        chebi_filled_db +=1

                index_metabolite += 1

        return (model,index_metabolite,chebi_filled_db)


    def annotate_reactions(self, model, db_bigg_rhea,reaction_id,reaction_name):
        index_reactions = 0
        rhea_filled_db = 0
        ecnumber_filled_db = 0

        for reaction in model.reactions:
            if (reaction_name == "BiGG"):
                bigg = reaction.name
            elif(reaction_id == "BiGG"):
                bigg = reaction.id
            #We search into the database we created
            if (bigg in db_bigg_rhea.BIGG.values):
                index_bigg = db_bigg_rhea.index[(db_bigg_rhea['BIGG'] == bigg)].tolist()[0]
                try:
                    rhea = reaction.annotation["rhea"]
                except :
                    id_rhea= db_bigg_rhea["RHEA"][index_bigg]
                    #if there is not a str, then it's nan, but we don't want to add an annotation "nan"
                    if(isinstance(id_rhea, str)):
                        reaction.annotation["rhea"] = id_rhea
                        rhea_filled_db +=1
                    try:
                        ec_number = reaction.annotation["ec-number"]
                    except :
                        id_ecnumber= db_bigg_rhea["EC-number"][index_bigg]
                        #if there is not a str, then it's nan, but we don't want to add an annotation "nan"
                        if(isinstance(id_ecnumber, str)):
                            reaction.annotation["ec-number"] = id_ecnumber
                            ecnumber_filled_db +=1
            index_reactions+= 1
        return (model, index_reactions,rhea_filled_db,ecnumber_filled_db)
