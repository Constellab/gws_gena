# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import pandas
from gws_core import (ConfigParams, InputSpec, ListParam, OutputSpec, Table,
                      Task, TaskInputs, TaskOutputs, task_decorator)

from .koa_result import KOAResult


@task_decorator("KOAResultExtractor", human_name="KOA result extractor",
                short_description="Extractor a list of fluxes as a table")
class KOAResultExtractor(Task):
    """
    KOA result extractor.
    """

    input_specs = {
        'koa_result': InputSpec(KOAResult, human_name="KOA result tables", short_description="The KOA result tables")
    }
    output_specs = {
        'table': OutputSpec(Table, human_name="Extracted table", short_description="The extracted table")
    }
    config_specs = {
        'fluxes_to_extract':
        ListParam(
            default_value=[], human_name="Fluxes to extract",
            short_description="The list of fluxes to extract")}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        koa_result = inputs["koa_result"]
        fluxes_to_extract: List = params.get_value("fluxes_to_extract")

        data = []
        for flux_name in fluxes_to_extract:
            for ko_id in koa_result.get_ko_ids():
                df = koa_result.get_flux_dataframe(ko_id).loc[[flux_name], :]
                df["ko_id"] = ko_id
                df["reaction_id"] = df.index
                df = df[["ko_id", "reaction_id", "value", "lower_bound", "upper_bound"]]
                data.append(df)

        data = pandas.concat(data, axis=0)
        data.reset_index(drop=True, inplace=True)
        table = Table(data)
        return {'table': table}