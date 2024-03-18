"""Command class for the CLI module"""

from abc import ABC, abstractmethod
from typing import Union, Optional


class Command(ABC):
    """Command class for the CLI module.

    The Command class hosts the possibility to execute commands.
    This is an abstract class for the commands. Actual functions of commands are to be defined in the specialised
    command classes. Depending on the type of command that is entered in the CLI, this class will make sure the correct
    command is executed.

    """

    @abstractmethod
    def execute(self, command_name: str, argument: Optional[Union[str, int]] = None):
        """Executes the command given by the CLI.

        Executes the command called `command_name`. If necessary, `argument` can be used to pass required parameters to
        the executable specified command.

        Parameters
        ----------
        command_name : str
            The name of the command to execute. An error will be thrown when the specified command does not exist for
            that command type.

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
