import os
from gws_core import (CondaShellProxy, MessageDispatcher)


class CobraEnvCondaHelper():
    ENV_DIR_NAME = "CobraCondaShellProxy"
    ENV_FILE_PATH = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "cobra_env_conda.yml"
    )

    @classmethod
    def create_proxy(cls, message_dispatcher: MessageDispatcher = None):
        return CondaShellProxy(cls.ENV_DIR_NAME, cls.ENV_FILE_PATH, message_dispatcher=message_dispatcher)
