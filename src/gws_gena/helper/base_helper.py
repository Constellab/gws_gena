# Gencovery software - All rights reserved
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BadRequestException, Logger, Task


class BaseHelper:
    """ BaseHelper """

    _task: Task = None

    def attach_task(self, task):
        """ attach task """
        if task is not None and not isinstance(task, Task):
            raise BadRequestException("The task must be a Task")
        self._task = task

    def log_info_message(self, message):
        if self._task:
            self._task.log_success_message(message)
        else:
            Logger.info(message)

    def log_success_message(self, message):
        if self._task:
            self._task.log_success_message(message)
        else:
            Logger.success(message)

    def log_warning_message(self, message):
        if self._task:
            self._task.log_warning_message(message)
        else:
            Logger.warning(message)

    def log_error_message(self, message):
        if self._task:
            self._task.log_error_message(message)
        else:
            Logger.error(message)

    def update_progress_value(self, value: float, message: str):
        if self._task:
            self._task.update_progress_value(value, message)
