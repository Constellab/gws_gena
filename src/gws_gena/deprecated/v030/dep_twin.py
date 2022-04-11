from gws_core import File, resource_decorator


@resource_decorator("TwinContextFile", human_name="TwinContextFile",
                    hide=True, deprecated_since='0.3.1', deprecated_message="Use simple file instead")
class TwinContextFile(File):
    pass
