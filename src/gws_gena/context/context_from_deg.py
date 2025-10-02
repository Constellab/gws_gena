import re
import pandas as pd
from gws_core import (ConfigParams, InputSpec, InputSpecs, OutputSpec,
                      OutputSpecs, Task, TaskInputs, TaskOutputs,
                      task_decorator, ConfigSpecs, Table, StrParam)
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
        "deg_augmented": OutputSpec(Table, human_name="DEG with reactions")})

    config_specs = ConfigSpecs({
        "gene_id_column": StrParam(default_value="gene_id", human_name="Gene ID column name")
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # Load the JSON model
        network: Network = inputs["network"]
        network_dict = network.dumps()

        deg_file : Table = inputs["deg"]
        df_deg = deg_file.get_data()

        # Get the gene ID column name from parameters
        gene_id_column = params["gene_id_column"]

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

        # return the output
        return {"deg_augmented" : Table(df_deg_with_reaction)}

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
