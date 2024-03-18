"""StatCommand class for the CLI module"""
from typing import Union, Optional

from cli.command import Command


class StatCommand(Command):
    """StatCommand class for the CLI module.

    The StatCommand class hosts the possibility to execute commands related to statistics.
    This class contains the commands for getting certain statistics not found in other classes and for showing the
    statistics.

    """

    def get_eta(self):
        """Gets the Estimated Time of Arrival.

        Returns
        -------
        eta : float
            Estimated Time of Arrival.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "ETA retrieved successfully"
        raise NotImplementedError()

    def show_statistics(self):
        """Gets the updated statistics.

        Gets all the statistics for the user to see; these statistics include: Start Time of the workday, end time of
        the workday, ETA, platform name, thread name, max thread age, max thread length, link follow policy, reading
        speed range, start time of next interruption, start time of next break, timezone, nr. of web pages, resources
        (CPU, memory, storage)

        Returns
        -------
        stats : str
            The statistics listed above, along with their values.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Statistics shown successfully"
        raise NotImplementedError()

    # This is a could
    def get_resources(self):
        """Gets the resources currently in use.

        Gets the CPU, Memory and Storage currently in use by the crawler.

        Returns
        -------
        resources : str
            The CPU, Memory and Storage in use.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Resources retrieved successfully"
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
