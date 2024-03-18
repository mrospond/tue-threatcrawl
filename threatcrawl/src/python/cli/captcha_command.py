"""CaptchaCommand class for the CLI module"""
from typing import Union

from cli.command import Command
from utils import Logger


class CaptchaCommand(Command):
    """CaptchaCommand class for the CLI module.

    The CaptchaCommand class deals with terminal interactions with captchas.
    This class currently contains a function to continue execution
    after CaptchaSolver when text "resume" is entered.

    Attributes
    ----------
    command_list : Dictionary
        dictionary for the commands
    solved: Threading.Condition
        resume condition to communicate the crawler that the CAPTCHA has been solved and crawler execution can resume.
    """

    def __init__(self, solved):
        self.command_list = {
            'solved': self.solved
        }
        self.solved = solved

    def solved(self):
        """Catches the resume input from keyboard for continuing crawling after solving a captcha.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """

        Logger.log("captcha", "Captcha solved, resuming execution.")
        self.solved.acquire()
        self.solved.notify()
        self.solved.release()

    def execute(self, command_name: str, argument: Union[str, int, None] = None):
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

        self.command_list[command_name]()
