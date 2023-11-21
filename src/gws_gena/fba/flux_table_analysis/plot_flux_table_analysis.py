import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from gws_core import (BoolParam, ConfigParams, File, FloatParam, InputSpec,
                      InputSpecs, OutputSpec, OutputSpecs, PlotlyResource,
                      StrParam, Table, Task, TaskInputs, TaskOutputs,
                      task_decorator)


@task_decorator("PlotFluxTableAnalysis", human_name="Flux Table Analysis",
                short_description="This task permits to plot a graph to analyse two fluxes tables from FBA."
                "This task takes two fluxes tables and a file containing a column with the modified reactions in input."
                "Gives a plot and a table in output.")
class PlotFluxTableAnalysis(Task):
    """
    Flux Table Analysis class

    This task permits to plot a graph to analyse two fluxes tables from FBA.
    Based on the log2(Fold change) of these fluxes, tag the fluxes according to whether they are more or less expressed in condition 2 than in condition 1.
    The threshold value entered in the parameters helps to discriminate the different groups.

    This task takes two fluxes tables and a file containing at least a column with the modified reactions in input.

    Gives a scatter plot with coloured points and a table in output.
    """

    input_specs = InputSpecs({'flux_table_condition1':  InputSpec(Table),
                              'flux_table_condition2':  InputSpec(Table),
                              'file_modified_reactions':  InputSpec(File)})

    output_specs = OutputSpecs({'plot': OutputSpec(PlotlyResource),
                                'table_changement': OutputSpec(Table)})

    config_specs = {'name_condition1': StrParam(short_description="Name of the condition 1"),
                    'name_condition2': StrParam(short_description="Name of the condition 2"),
                    'pattern': StrParam(short_description="Pattern before the reaction id in the flux table"),
                    'column_reaction_id': StrParam(short_description="Name of the column containing the reactions"),
                    'threshold': FloatParam(default_value=2, short_description="Threshold for the log2(Fold Change)"),
                    'log_x': BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Axis x in log",
                                       short_description="True to consider the x axis as logarithmic. False otherwise."),
                    'log_y': BoolParam(default_value=False, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Axis y in log",
                                       short_description="True to consider the y axis as logarithmic. False otherwise.")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        flux_table_condition1: Table = inputs["flux_table_condition1"]
        flux_table_condition2: Table = inputs["flux_table_condition2"]
        file_modified_reactions: File = inputs["file_modified_reactions"]

        name_condition1 = params["name_condition1"]
        name_condition2 = params["name_condition2"]
        pattern = params["pattern"]
        column_reaction_id = params["column_reaction_id"]
        threshold = params["threshold"]
        log_x = params["log_x"]
        log_y = params["log_y"]

        # We load the flux tables and the reactions modified
        flux_condition1 = flux_table_condition1.get_data()
        flux_condition1.reset_index(level=0, inplace=True)
        flux_condition1.columns = ["reaction", "value", "lower_bound", "upper_bound"]

        flux_condition2 = flux_table_condition2.get_data()
        flux_condition2.reset_index(level=0, inplace=True)
        flux_condition2.columns = ["reaction", "value", "lower_bound", "upper_bound"]

        list_reactions_modified = pd.read_csv(file_modified_reactions.path, sep=',')

        # We remove the pattern added by the FBA task
        flux_condition1['reaction'] = flux_condition1['reaction'].str.replace(re.escape(pattern), '')
        flux_condition2['reaction'] = flux_condition2['reaction'].str.replace(re.escape(pattern), '')

        # We create the dataframe
        columns_changements = ("Tag", "Reaction", "flux_" + name_condition1, "flux_" + name_condition2)
        table_changements = pd.DataFrame(columns=columns_changements)

        for i in range(0, len(flux_condition1["value"])-1):
            flux_condition1_value = flux_condition1["value"][i]
            flux_condition2_value = flux_condition2["value"][i]
            reaction_id = flux_condition1["reaction"][i]
            # We compute the fold change
            fold_change = np.log2(flux_condition2_value/flux_condition1_value)

            # We tag each reaction depending the fluxes values
            if reaction_id in list_reactions_modified[column_reaction_id].values:
                tag = "Modified flux"
            # If the reaction was created by the FBA, it's also tagged with "Modified flux"
            elif reaction_id.startswith('measure'):
                tag = "Modified flux"

            elif flux_condition2_value > 0 and flux_condition1_value > 0:
                if fold_change > threshold:
                    tag = name_condition2 + " superior"
                elif fold_change < - threshold:
                    tag = name_condition2 + " inferior"
                else:
                    tag = "Equal fluxes"

            elif flux_condition2_value < 0 and flux_condition1_value < 0:
                if fold_change > threshold:
                    tag = name_condition2 + " inferior"
                elif fold_change < - threshold:
                    tag = name_condition2 + " superior"
                else:
                    tag = "Equal fluxes"

            elif flux_condition2_value < 0 and flux_condition1_value > 0:
                tag = name_condition2 + " inferior"

            elif flux_condition2_value > 0 and flux_condition1_value < 0:
                tag = name_condition2 + " superior"

            row = pd.DataFrame(
                [[tag, reaction_id, flux_condition1_value, flux_condition2_value]],
                columns=columns_changements)
            table_changements = pd.concat([table_changements, row])

        # Write the output file in the target folder
        result_path = "table_changements.csv"
        table_changements.to_csv(result_path, index=False)

        # PLOT
        source = Table(table_changements).get_data()
        # Scatter plot
        target = px.scatter(source, x="flux_" + name_condition1, y="flux_" + name_condition2,
                            color='Tag', log_x=log_x, log_y=log_y)

        # Add bisector line
        min_val = min(source["flux_" + name_condition1].min(), source["flux_" + name_condition2].min())
        max_val = max(source["flux_" + name_condition1].max(), source["flux_" + name_condition2].max())
        target.add_shape(
            type='line',
            x0=min_val,
            y0=min_val,
            x1=max_val,
            y1=max_val,
            line=dict(color='black', dash='dash')
        )

        # Count the number of rows for each Tag type
        tag_counts = source['Tag'].value_counts()

        # Create annotation for each Tag count
        annotations = []
        for i, (tag, count) in enumerate(tag_counts.iteritems()):
            annotations.append(go.layout.Annotation(
                x=max_val,
                y=len(tag_counts) - i,
                text=f"{tag}: {count}",
                showarrow=False,
                font=dict(color='black'),
                xanchor='left',
                yanchor='top',
                xshift=10,
                yshift=-20*(i+1)
            ))

        # Add annotations to the layout
        target.update_layout(
            annotations=annotations
        )

        return {'plot': PlotlyResource(target),
                'table_changement': Table(table_changements)}
