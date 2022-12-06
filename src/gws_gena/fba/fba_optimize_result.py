# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict

from gws_core import SerializableObjectJson


class FBAOptimizeResult(SerializableObjectJson):
    """
    OptimizeResult class.

    A simple proxy of SciPy OptimizeResult
    """

    _data: dict = None

    def __init__(self, data: dict = None):
        if data is None:
            self._data = {}
            return
        self._data = data

    @property
    def x(self):
        return self._data.get("x")

    @x.setter
    def x(self, x):
        self._data["x"] = x

    @property
    def xmin(self):
        return self._data.get("xmin")

    @xmin.setter
    def xmin(self, xmin):
        self._data["xmin"] = xmin

    @property
    def xmax(self):
        return self._data.get("xmax")

    @xmax.setter
    def xmax(self, xmax):
        self._data["xmax"] = xmax

    @property
    def x_names(self):
        return self._data.get("x_names")

    @x_names.setter
    def x_names(self, x_names):
        self._data["x_names"] = x_names

    @property
    def constraints(self):
        return self._data.get("constraints")

    @constraints.setter
    def constraints(self, constraints):
        self._data["constraints"] = constraints

    @property
    def constraint_names(self):
        return self._data.get("constraint_names")

    @constraint_names.setter
    def constraint_names(self, constraint_names):
        self._data["constraint_names"] = constraint_names

    @property
    def niter(self):
        return self._data.get("niter")

    @niter.setter
    def niter(self, niter):
        self._data["niter"] = niter

    @property
    def message(self):
        return self._data.get("message")

    @message.setter
    def message(self, message):
        self._data["message"] = message

    @property
    def success(self):
        return self._data.get("success")

    @success.setter
    def success(self, success):
        self._data["success"] = success

    @property
    def status(self):
        return self._data.get("status")

    @status.setter
    def status(self, status):
        self._data["status"] = status

    def serialize(self) -> Dict[str, Any]:
        """
        Serialize
        """

        return self._data

    @ classmethod
    def deserialize(cls, data: Dict[str, Any]) -> 'OptimizeResult':
        """ Deserialize """
        if data is None:
            return {}

        return cls(data)
