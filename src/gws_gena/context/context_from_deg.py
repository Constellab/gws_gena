import re
import pandas as pd
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator, ConfigSpecs, Table, StrParam, FloatParam)
from gws_gena import Network


@task_decorator("ContextFromDEG", human_name="Context from DEG")
class ContextFromDEG(Task):
    """
    Context from DEG

    """

    input_specs = InputSpecs({
        "deg": InputSpec(Table, human_name="DEG"),
        "network": InputSpec(Network, human_name="Network"),
    })
    output_specs = OutputSpecs({
        "deg_augmented": OutputSpec(Table, human_name="DEG with reactions"),
        "context_flux_table_low_AGS_vs_CT": OutputSpec(Table, human_name="Context flux table low AGS vs CT"),
        "context_flux_table_high_AGS_vs_CT": OutputSpec(Table, human_name="Context flux table high AGS vs CT"),
        "list_reactions_modified": OutputSpec(Table, human_name="List of reactions modified"),
    })

    config_specs = ConfigSpecs({
        "gene_id_column": StrParam(default_value="gene_id", human_name="Gene ID column name"),
        "log2_fold_change_column": StrParam(default_value="avg_log2FC", human_name="Log2 fold change column name"),
        "threshold": FloatParam(default_value=0.25, human_name="Threshold for log fold change", visibility=StrParam.PROTECTED_VISIBILITY),
        "lower_bound_high": FloatParam(default_value=0.5, human_name="Lower bound high", visibility=StrParam.PROTECTED_VISIBILITY),
        "upper_bound_high": FloatParam(default_value=1000, human_name="Upper bound high", visibility=StrParam.PROTECTED_VISIBILITY),
        "target_low": FloatParam(default_value=0, human_name="Target low", visibility=StrParam.PROTECTED_VISIBILITY),
        "lower_bound_low": FloatParam(default_value=0, human_name="Lower bound low", visibility=StrParam.PROTECTED_VISIBILITY),
        "upper_bound_low": FloatParam(default_value=0, human_name="Upper bound low", visibility=StrParam.PROTECTED_VISIBILITY),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # Parameters
        gene_id_column = params["gene_id_column"]
        log2_fold_change_column = params["log2_fold_change_column"]
        threshold = params["threshold"]
        lower_bound_high = params["lower_bound_high"]
        upper_bound_high = params["upper_bound_high"]
        target_low = params["target_low"]
        lower_bound_low = params["lower_bound_low"]
        upper_bound_low = params["upper_bound_low"]

        # Load the JSON model
        network: Network = inputs["network"]
        network_dict = network.dumps()

        deg_file : Table = inputs["deg"]
        df_deg = deg_file.get_data()

        # Ensure the gene_id column exists and convert to string
        if gene_id_column not in df_deg.columns:
            raise ValueError(f"Column '{gene_id_column}' not found in DEG table")
        # Convert the gene_id column to string, handling float values properly
        df_deg[gene_id_column] = df_deg[gene_id_column].apply(self.convert_to_clean_string)

        # Also ensure Gene_ID in associations are strings for proper matching
        # Create a list to store associations between gene IDs and reaction IDs
        associations = []

        # Iterate through each reaction in the model
        for reaction in network_dict["reactions"]:
            # Use a regular expression to extract gene IDs
            gene_ids = re.findall(r'(\b\w+\b)', reaction["gene_reaction_rule"])
            for gene_id in gene_ids:
                if gene_id not in ["or", "and"]:
                    associations.append((gene_id, reaction["id"]))

        # Convert the list of associations to a DataFrame
        df_gene_reaction = pd.DataFrame(associations, columns=["Gene_ID", "Reaction_ID"])
        df_gene_reaction["Gene_ID"] = df_gene_reaction["Gene_ID"].astype(str)

        # Create a new DataFrame to store the results
        df_deg_with_reaction = pd.DataFrame(columns=df_deg.columns.tolist() + ['ID_reaction'])

        # Iterate through each "gene_id" in `df_deg`
        for _, row in df_deg.iterrows():
            gene_id = row[gene_id_column]
            matching_reactions = df_gene_reaction[df_gene_reaction['Gene_ID'] == gene_id]['Reaction_ID'].tolist()

            # If there are matching reactions, add them to the resulting DataFrame
            if matching_reactions:
                for reaction in matching_reactions:
                    new_row = row.copy()
                    new_row['ID_reaction'] = reaction
                    df_deg_with_reaction = pd.concat([df_deg_with_reaction, pd.DataFrame([new_row])], ignore_index=True)
            else:
                # If no reactions match, keep the row as-is
                new_row = row.copy()
                df_deg_with_reaction = pd.concat([df_deg_with_reaction, pd.DataFrame([new_row])], ignore_index=True)



        # We create the context flux tables
        context_flux_table_low_AGS_vs_CT, context_flux_table_high_AGS_vs_CT, list_reactions_modified = self.creation_context_flux_table(df_deg_with_reaction, log2_fold_change_column, gene_id_column, threshold, lower_bound_high, upper_bound_high, target_low, lower_bound_low, upper_bound_low)


        # TODO trouver un moyen de combiner les 2 contexts

        # return the output
        return {"deg_augmented" : Table(df_deg_with_reaction),
                "context_flux_table_low_AGS_vs_CT": Table(context_flux_table_low_AGS_vs_CT),
                "context_flux_table_high_AGS_vs_CT": Table(context_flux_table_high_AGS_vs_CT),
                "list_reactions_modified": Table(list_reactions_modified)}

    # Convert to string, handling float values properly
    def convert_to_clean_string(self, value):
        if pd.isna(value):
            return str(value)
        try:
            # If it's a float that represents an integer, convert to int first
            float_val = float(value)
            if float_val.is_integer():
                return str(int(float_val))
            else:
                return str(float_val)
        except (ValueError, TypeError):
            return str(value)


    def creation_context_flux_table(self, df_deg_with_reaction, fold_change_column_name, gene_id_column, threshold, lower_bound_high, upper_bound_high, target_low, lower_bound_low, upper_bound_low):
        columns_context_flux_table = ("ID_reaction", "gene_id", "target", "lower_bound", "upper_bound", "confidence_score")
        context_flux_table_low_condition2 = pd.DataFrame(columns=columns_context_flux_table)
        context_flux_table_high_condition2 = pd.DataFrame(columns=columns_context_flux_table)

        number = 0
        list_reactions_modified = pd.DataFrame(columns=("number", "reaction", "flux tracability"))

        for line in df_deg_with_reaction.index:
            if (df_deg_with_reaction[fold_change_column_name][line] < -threshold):
                reaction = df_deg_with_reaction["ID_reaction"][line]
                gene = df_deg_with_reaction[gene_id_column][line]
                confidence = 1

                target_condition2 = target_low
                lower_bound_condition2 = lower_bound_low
                upper_bound_condition2 = upper_bound_low

                row2 = pd.DataFrame([[reaction, gene, target_condition2, lower_bound_condition2, upper_bound_condition2, confidence]], columns=columns_context_flux_table)
                context_flux_table_low_condition2 = pd.concat([context_flux_table_low_condition2, row2])

                row3 = pd.DataFrame([[number, reaction, "low"]], columns=("number", "reaction", "flux tracability"))
                list_reactions_modified = pd.concat([list_reactions_modified, row3])
                number += 1

            elif (df_deg_with_reaction[fold_change_column_name][line] > threshold):
                reaction = df_deg_with_reaction["ID_reaction"][line]
                gene = df_deg_with_reaction[gene_id_column][line]
                confidence = 1

                target_condition2 = 0.36 # TODO voir comment faire
                lower_bound_condition2 = lower_bound_high
                upper_bound_condition2 = upper_bound_high

                row2 = pd.DataFrame([[reaction, gene, target_condition2, lower_bound_condition2, upper_bound_condition2, confidence]], columns=columns_context_flux_table)
                context_flux_table_high_condition2 = pd.concat([context_flux_table_high_condition2, row2])

                row3 = pd.DataFrame([[number, reaction, "high"]], columns=("number", "reaction", "flux tracability"))
                list_reactions_modified = pd.concat([list_reactions_modified, row3])
                number += 1

        # It seems that we have to remove duplicates before using it in a FBA context
        context_flux_table_low_condition2 = context_flux_table_low_condition2.drop_duplicates(subset='ID_reaction', keep='first')
        context_flux_table_high_condition2 = context_flux_table_high_condition2.drop_duplicates(subset='ID_reaction', keep='first')

        return context_flux_table_low_condition2, context_flux_table_high_condition2, list_reactions_modified