import os

from gws_core import Settings


class DataProvider:
    @classmethod
    def get_test_data_dir(cls) -> str:
        test_data_dir = Settings.get_instance().get_variable("gws_gena", "testdata_dir")
        if test_data_dir is None:
            raise ValueError("testdata_dir is not configured in settings")
        return test_data_dir

    @classmethod
    def get_test_data_path(cls, path: str) -> str:
        return os.path.join(cls.get_test_data_dir(), path)
