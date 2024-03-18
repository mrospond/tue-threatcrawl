"""ExportCommand class for the CLI module"""
from typing import Union, Optional

from cli.command import Command


class ExportCommand(Command):
    """ExportCommand class for the CLI module.

    The ExportCommand class contains the command for exporting links.

    """

    def export_links(self):
        """Exports links encountered during crawling to a file.

        When called, the links to other platforms that are encountered during crawling to a file are exported.

        Returns
        -------
        links : str
            List of links that are exported.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Links exported successfully"
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
        pass
