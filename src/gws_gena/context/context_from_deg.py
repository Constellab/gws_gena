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
        "context_flux_table": OutputSpec(Table, human_name="Context flux table"),
        "list_reactions_modified": OutputSpec(Table, human_name="List of reactions modified"),
    })

    config_specs = ConfigSpecs({
        "gene_id_column": StrParam(default_value="gene_id", human_name="Gene ID column name"),
        "log2_fold_change_column": StrParam(default_value="avg_log2FC", human_name="Log2 fold change column name"),
        "threshold": FloatParam(default_value=0.25, human_name="Threshold for log fold change", visibility=StrParam.PROTECTED_VISIBILITY),
        "target_high": FloatParam(default_value=0.36, human_name="Target high", visibility=StrParam.PROTECTED_VISIBILITY), # TODO voir pour mettre dans la doc que ça devrait être la médiane de la condition normale -> à vérifier
        "lower_bound_high": FloatParam(default_value=0.5, human_name="Lower bound high", visibility=StrParam.PROTECTED_VISIBILITY),
        "upper_bound_high": FloatParam(default_value=1000, human_name="Upper bound high", visibility=StrParam.PROTECTED_VISIBILITY),
        "target_low": FloatParam(default_value=0, human_name="Target low", visibility=StrParam.PROTECTED_VISIBILITY),
        "lower_bound_low": FloatParam(default_value=0, human_name="Lower bound low", visibility=StrParam.PROTECTED_VISIBILITY),
        "upper_bound_low": FloatParam(default_value=0, human_name="Upper bound low", visibility=StrParam.PROTECTED_VISIBILITY),
        "confidence": FloatParam(default_value=1, human_name="Confidence score", visibility=StrParam.PROTECTED_VISIBILITY),
    })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        # Parameters
        gene_id_column = params["gene_id_column"]
        log2_fold_change_column = params["log2_fold_change_column"]
        threshold = params["threshold"]
        target_high = params["target_high"]
        lower_bound_high = params["lower_bound_high"]
        upper_bound_high = params["upper_bound_high"]
        target_low = params["target_low"]
        lower_bound_low = params["lower_bound_low"]
        upper_bound_low = params["upper_bound_low"]
        confidence = params["confidence"]

        # Load the JSON model
        network: Network = inputs["network"]
        network_dict = network.dumps()

        deg_file : Table = inputs["deg"]
        df_deg = deg_file.get_data()

        # Ensure the gene_id column exists and convert to string
        if gene_id_column not in df_deg.columns:
            raise ValueError(f"Column '{gene_id_column}' not found in DEG table")
        if log2_fold_change_column not in df_deg.columns:
            raise ValueError(f"Column '{log2_fold_change_column}' not found in DEG table")

        # Convert the gene_id column to string, handling float values properly
        df_deg[gene_id_column] = df_deg[gene_id_column].apply(self.convert_to_clean_string)

        # Create context
        columns_context_flux_table = ("ID_reaction", "target", "lower_bound", "upper_bound", "confidence_score")
        context_flux_table = pd.DataFrame(columns=columns_context_flux_table)

        list_reactions_modified = pd.DataFrame(columns=("Reaction", "Flux traceability"))
        # Iterate through each reaction in the model
        for reaction in network_dict["reactions"]:
            if reaction["gene_reaction_rule"]:
                # Evaluate the boolean expression for gene reaction rule
                value = self.evaluate_gene_reaction_rule(reaction["gene_reaction_rule"], df_deg, gene_id_column, log2_fold_change_column)

                if value is not None:
                    if value < -threshold:
                        target_condition2 = target_low
                        lower_bound_condition2 = lower_bound_low
                        upper_bound_condition2 = upper_bound_low

                        row2 = pd.DataFrame([[reaction["id"], target_condition2, lower_bound_condition2, upper_bound_condition2, confidence]], columns=columns_context_flux_table)
                        context_flux_table = pd.concat([context_flux_table, row2])

                        row_reactions_modified = pd.DataFrame([[reaction["id"], "low"]], columns=("Reaction", "Flux traceability"))
                        list_reactions_modified = pd.concat([list_reactions_modified, row_reactions_modified])

                    elif (value > threshold):
                        target_condition2 = target_high
                        lower_bound_condition2 = lower_bound_high
                        upper_bound_condition2 = upper_bound_high

                        row2 = pd.DataFrame([[reaction["id"], target_condition2, lower_bound_condition2, upper_bound_condition2, confidence]], columns=columns_context_flux_table)
                        context_flux_table = pd.concat([context_flux_table, row2])

                        row_reactions_modified = pd.DataFrame([[reaction["id"], "high"]], columns=("Reaction", "Flux traceability"))
                        list_reactions_modified = pd.concat([list_reactions_modified, row_reactions_modified])
            else:
                # We don't have any information, we don't add this reaction in the context
                pass


        # return the output
        return {"context_flux_table": Table(context_flux_table),
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

    def evaluate_gene_reaction_rule(self, rule, df_deg, gene_id_column, log2_fold_change_column):
        """
        Evaluate a boolean gene reaction rule and return the appropriate log2 fold change value.
        For OR operations: take the maximum value
        For AND operations: take the minimum value
        """
        if not rule or pd.isna(rule):
            return None

        # Extract all gene IDs from the rule
        gene_ids = re.findall(r'\b[A-Za-z0-9_]+\b', rule)
        gene_ids = [gene_id for gene_id in gene_ids if gene_id not in ["or", "and"]]

        # Get values for all genes in the rule
        gene_values = {}
        for gene_id in gene_ids:
            gene_data = df_deg[df_deg[gene_id_column] == gene_id]
            if not gene_data.empty:
                gene_values[gene_id] = gene_data[log2_fold_change_column].iloc[0]

        if not gene_values:
            return None

        # Evaluate the boolean expression
        return self._evaluate_boolean_expression(rule, gene_values)

    def _evaluate_boolean_expression(self, expression, gene_values):
        """
        Recursively evaluate a boolean expression with gene values.
        """
        # Remove extra spaces
        expression = ' '.join(expression.split())

        # Handle parentheses first
        while '(' in expression:
            # Find the innermost parentheses
            start = -1
            for i, char in enumerate(expression):
                if char == '(':
                    start = i
                elif char == ')':
                    if start != -1:
                        # Evaluate the expression inside parentheses
                        inner_expr = expression[start+1:i]
                        inner_value = self._evaluate_boolean_expression(inner_expr, gene_values)
                        # Replace the parentheses with the result
                        expression = expression[:start] + str(inner_value) + expression[i+1:]
                        break

        # Split by 'or' operations (lower precedence)
        or_parts = expression.split(' or ')
        if len(or_parts) > 1:
            or_values = []
            for part in or_parts:
                part_value = self._evaluate_boolean_expression(part.strip(), gene_values)
                if part_value is not None:
                    or_values.append(part_value)
            return max(or_values) if or_values else None

        # Split by 'and' operations (higher precedence)
        and_parts = expression.split(' and ')
        if len(and_parts) > 1:
            and_values = []
            for part in and_parts:
                part_value = self._evaluate_boolean_expression(part.strip(), gene_values)
                if part_value is not None:
                    and_values.append(part_value)
            return min(and_values) if and_values else None

        # Base case: single gene or numeric value
        expression = expression.strip()
        if expression in gene_values:
            return gene_values[expression]


        # Try to parse as float (for expression that correspond to gene expression and not gene id)
        try:
            float_val = float(expression)
            # Check if it's a float string (contains decimal point) -> it's gene expression
            if '.' in expression:
                return float_val
        except ValueError:
            pass


        return None