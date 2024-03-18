"""ConfigCommand class for the CLI module"""
from typing import Union, Optional

from cli.command import Command


class ConfigCommand(Command):
    """ConfigCommand class for the CLI module.

    The ConfigCommand class hosts the possibility to execute commands related to configurations.
    This class contains the commands for setting certain configurations and showing the current configuration.

    """

    # This is a should
    def set_max_thread_age(self, age):
        """Sets the maximum thread age to `age`.

        Parameters
        ----------
        age : float
            The age to which to set the maximum thread age.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return = "Maximum thread age " + str(age) + " set successfully"
        raise NotImplementedError

    # This is a should
    def set_max_thread_length(self, length):
        """Sets the maximum thread length to `length`.

        Parameters
        ----------
        length : float
            The length to which to set the maximum thread length.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return = "Maximum thread length " + str(length) + " set successfully"
        raise NotImplementedError()

    # This is a should
    def toggle_link_policy(self):
        """Toggles the link policy that the crawler uses.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Link policy toggled successfully"
        raise NotImplementedError()

    # This is a should
    def show_updated_configuration(self):
        """Gets the updated configuration.

        Returns
        -------
        configurations : str
            The list of configurations and their current values.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Updated configurations shown successfully"
        raise NotImplementedError()

    # This is a could
    def set_max_reading_speed(self, speed):
        """Sets the reading speed to `speed`.

        Parameters
        ----------
        speed : float
            The speed to which to set the reading speed.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Maximum reading speed " + str(speed) + " set successfully"
        raise NotImplementedError()

    # Override
    def execute(self, command_name: str, argument: Optional[Union[str, int]] = None):
        """Executes the command given by the CLI.

        Executes the command called `command_name`. If necessary, `argument` can be used to pass required parameters to
        the executable specified command.

        Parameters
        ----------
        command_name : str
            The name of the command to execute. An error will be thrown when the specified command does not exist for
            this command type.

        argument: str | int | None, default: None
            The argument used for a command. Some commands may require an integer, while others use a string. If no
            parameter is required, pass None.

        Raises
        ------
        NonExistentCommandException
            The given command name could not be located in the given command type.
        BadArgumentException
            The given argument for the given command is invalid.
        CommandFailureException
            The command could not be executed
        """
        raise NotImplementedError()
