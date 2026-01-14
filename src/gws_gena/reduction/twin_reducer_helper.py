# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import MessageDispatcher, ShellProxy


class TwinReducerHelper:
    """
    Helper class for TwinReducer task to provide shell proxy functionality
    for installing Java and other system dependencies.
    """

    @classmethod
    def create_proxy(cls, message_dispatcher: MessageDispatcher | None = None):
        """
        Create a shell proxy for running system commands.

        Args:
            message_dispatcher: Optional message dispatcher for logging

        Returns:
            ShellProxy: Shell proxy instance for running commands
        """
        if message_dispatcher is None:
            message_dispatcher = MessageDispatcher()
        return ShellProxy(message_dispatcher=message_dispatcher)

    @classmethod
    def install_java(cls, shell_proxy: ShellProxy) -> bool:
        """
        Install Java JDK using the provided shell proxy.

        Args:
            shell_proxy: Shell proxy instance to use for commands

        Returns:
            bool: True if installation was successful, False otherwise
        """
        try:
            # Update package list
            result = shell_proxy.run("apt update", shell_mode=True)
            if result != 0:
                shell_proxy.log_error_message("[TwinReducerHelper] Failed to update package list")
                return False

            # Install Java JDK
            result = shell_proxy.run("apt -y install default-jdk", shell_mode=True)
            if result != 0:
                shell_proxy.log_error_message("[TwinReducerHelper] Failed to install Java JDK")
                return False
            return True

        except Exception as e:
            shell_proxy.log_error_message(
                f"[TwinReducerHelper] Error during Java installation: {str(e)}"
            )
            return False
