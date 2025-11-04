import sys
import pandas as pd
import re
from cobra.io import save_json_model, load_json_model

#Function to annotate metabolites
def annotate_metabolites(model, db_bigg_chebi, metabolites_id, metabolites_name):
    index_metabolite = 0
    chebi_filled_db = 0

    for metabolite in model.metabolites:
        # We give priority if there are BiGG identifiers
        if (metabolites_name == "BiGG" or metabolites_id == "BiGG"):
            if (metabolites_name == "BiGG"):
                bigg = metabolite.name
            elif (metabolites_id == "BiGG"):
                bigg = metabolite.id
            #If there is the id of the compartment at the end of the bigg id, we remove it
            bigg = re.sub(r'(_c$|_e$|_b$|_cm$|_cx$|_g$|_h$|_f$|_m$|_i$|_im$|_mm$|_l$|_n$|_p$|_r$|_s$|_env$|_u$|_um$|_v$|_x$|_y$|_w$)', '', bigg)
            # We search into the database we created
            if (bigg in db_bigg_chebi.BIGG.values):
                index_bigg = db_bigg_chebi.index[(db_bigg_chebi['BIGG'] == bigg)].tolist()[0]
                if 'chebi' not in metabolite.annotation:
                    id_chebi = db_bigg_chebi["CHEBI"][index_bigg]
                    metabolite.annotation["chebi"] = str(id_chebi)
                    chebi_filled_db += 1

            index_metabolite += 1

        elif (metabolites_name == "Literal_name" or metabolites_id == "Literal_name"):
            if (metabolites_name == "Literal_name"):
                name = metabolite.name.lower()
            elif (metabolites_id == "Literal_name"):
                name = metabolite.id.lower()
            # We search into the database we created
            if (name in db_bigg_chebi.Name.values):
                index_bigg = db_bigg_chebi.index[(db_bigg_chebi['Name'] == name)].tolist()[0]
                if 'chebi' not in metabolite.annotation:
                    id_chebi = db_bigg_chebi["CHEBI"][index_bigg]
                    metabolite.annotation["chebi"] = str(id_chebi)
                    chebi_filled_db += 1

            index_metabolite += 1

    return (model, index_metabolite, chebi_filled_db)

#Function to annotate reactions
def annotate_reactions(model, db_bigg_rhea, reaction_id, reaction_name):
    index_reactions = 0
    rhea_filled_db = 0
    ecnumber_filled_db = 0

    for reaction in model.reactions:
        if (reaction_name == "BiGG"):
            bigg = reaction.name
        elif (reaction_id == "BiGG"):
            bigg = reaction.id
        # We search into the database we created
        if (bigg in db_bigg_rhea.BIGG.values):
            index_bigg = db_bigg_rhea.index[(db_bigg_rhea['BIGG'] == bigg)].tolist()[0]

            if 'rhea' not in reaction.annotation:
                id_rhea = db_bigg_rhea["RHEA"][index_bigg]
                # if there is not a str, then it's nan, but we don't want to add an annotation "nan"
                if (isinstance(id_rhea, str)):
                    reaction.annotation["rhea"] = id_rhea
                    rhea_filled_db += 1
            if 'ec-number' not in reaction.annotation:
                id_ecnumber = db_bigg_rhea["EC-number"][index_bigg]
                # if there is not a str, then it's nan, but we don't want to add an annotation "nan"
                if (isinstance(id_ecnumber, str)):
                    reaction.annotation["ec-number"] = id_ecnumber
                    ecnumber_filled_db += 1

        index_reactions += 1
    return (model, index_reactions, rhea_filled_db, ecnumber_filled_db)


input_model = sys.argv[1]
output_path = sys.argv[2]
metabolites_id = sys.argv[3]
metabolites_name = sys.argv[4]
reaction_id = sys.argv[5]
reaction_name = sys.argv[6]
results_path = sys.argv[7]
db_metabolites_path = sys.argv[8]
db_reactions_path = sys.argv[9]

index_reactions = 0
index_metabolite = 0
chebi_filled_db = 0
rhea_filled_db = 0
ecnumber_filled_db = 0

# Load metabolic model
model = load_json_model(input_model)
# Load the database Reactions
db_bigg_rhea = pd.read_csv(db_reactions_path, sep='\t', dtype=str)

# Load the database Metabolites
db_bigg_chebi = pd.read_csv(db_metabolites_path, sep='\t', dtype=str)

# Metabolites
if (metabolites_id != "Other" or metabolites_name != "Other"):
    model, index_metabolite, chebi_filled_db = annotate_metabolites(
        model, db_bigg_chebi, metabolites_id, metabolites_name)

# Reactions
if (reaction_id != "Other" or reaction_name != "Other"):
    model, index_reactions, rhea_filled_db, ecnumber_filled_db = annotate_reactions(
        model, db_bigg_rhea, reaction_id, reaction_name)

#Create dataframe results
columns_results = ("Number reactions", "Rhea filled", "EC number filled", "Number metabolites", "ChEBI filled")
results = pd.DataFrame(columns=columns_results)
row = pd.DataFrame([[index_reactions, rhea_filled_db, ecnumber_filled_db,
                    index_metabolite, chebi_filled_db]], columns=columns_results)
results = pd.concat([results, row])

# Output
save_json_model(model, output_path)
results.to_csv(results_path)
