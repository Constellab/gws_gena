from gws_core import (PipShellProxy, MessageDispatcher)
import os


class PyOpenMsEnvHelper():
    ENV_DIR_NAME = "PyOpenMsShellProxy"
    ENV_FILE_PATH = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        "pyopenms_env.txt"
    )

    @classmethod
    def create_proxy(cls, message_dispatcher: MessageDispatcher = None):
        return PipShellProxy(cls.ENV_DIR_NAME, cls.ENV_FILE_PATH, message_dispatcher=message_dispatcher)