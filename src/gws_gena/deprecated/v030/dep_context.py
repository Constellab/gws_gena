from gws_core import (File, resource_decorator, Resource, task_decorator,
                        importer_decorator, exporter_decorator, Task,
                        ResourceExporter, ResourceImporter)


@resource_decorator("TwinContext", human_name="Twin Context", short_description="Context of metabolic network",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use Context instead")
class TwinContext(Resource):
    pass

@resource_decorator("TwinContextFile", human_name="TwinContextFile",
                    hide=True, deprecated_since='0.3.1', deprecated_message="")
class TwinContextFile(File):
    pass

@importer_decorator("TwinContextImporter", human_name="Twin context importer", source_type=File,
                    target_type=TwinContext, supported_extensions=[".json"],
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use ContextImporter instead")
class TwinContextImporter(ResourceImporter):
    pass

@task_decorator("TwinContextBuilder", human_name="Network context builder",
                short_description="Build a context of metabolic network using a flux table",
                hide=True, deprecated_since='0.3.1', deprecated_message="Use ContextBuilder instead")
class TwinContextBuilder(Task):
    pass