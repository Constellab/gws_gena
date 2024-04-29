
from json import dumps, loads
from typing import List

from gws_core import (BrickMigration, File, Folder, ResourceModel, TaskModel,
                      Version, brick_migration, Table)


@brick_migration('0.7.0', short_description='Replace specific tables types to Table')
class Migration070(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        typing_dict = {
            'RESOURCE.gws_gena.PhenotypeTable': Table._typing_name,
            'RESOURCE.gws_gena.ECTable': Table._typing_name,
            'RESOURCE.gws_gena.EntityIDTable': Table._typing_name,
            'RESOURCE.gws_gena.BiomassReactionTable': Table._typing_name,
            'RESOURCE.gws_gena.MediumTable': Table._typing_name,
            'RESOURCE.gws_gena.FluxTable': Table._typing_name,
        }

        for key, value in typing_dict.items():
            ResourceModel.replace_resource_typing_name(key, value)

        # replace the references in the tasks inputs and outputs specs
        tasks_models: List[TaskModel] = list(TaskModel.select())
        for task_model in tasks_models:
            for key, value in typing_dict.items():
                task_model.data = loads(dumps(task_model.data).replace(key, value))

            task_model.save(skip_hook=True)
