from gws_core import BadRequestException, Logger, MessageDispatcher


class BaseHelper:
    """BaseHelper"""

    _message_dispatcher: MessageDispatcher | None = None

    def attach_message_dispatcher(self, message_dispatcher):
        """attach task"""
        if message_dispatcher is not None and not isinstance(message_dispatcher, MessageDispatcher):
            raise BadRequestException("Invalid message dispatcher.")
        self._message_dispatcher = message_dispatcher

    def log_info_message(self, message):
        if self._message_dispatcher:
            self._message_dispatcher.notify_info_message(message)
        else:
            Logger.info(message)

    def log_warning_message(self, message):
        if self._message_dispatcher:
            self._message_dispatcher.notify_warning_message(message)
        else:
            Logger.warning(message)

    def log_error_message(self, message):
        if self._message_dispatcher:
            self._message_dispatcher.notify_error_message(message)
        else:
            Logger.error(message)

    def log_debug_message(self, message):
        if self._message_dispatcher:
            self._message_dispatcher.notify_debug_message(message)
        else:
            Logger.debug(message)

    def update_progress_value(self, value: float, message: str):
        if self._message_dispatcher:
            self._message_dispatcher.notify_progress_value(value, message)
