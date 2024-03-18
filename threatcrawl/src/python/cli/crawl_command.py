"""CrawlCommand class for the CLI module"""
from typing import Union, Optional

from cli.command import Command
from utils import Logger


class CrawlCommand(Command):
    """CrawlCommand class for the CLI module.

    The CrawlCommand class hosts the possibility to execute commands related to crawling.
    This class contains the commands for manually pausing, starting or terminating crawling, or skipping a page.

    Parameters
    ----------
    pause : Threading.Event
        pause event to pause the crawler
    terminate : Threading.Event
        terminate event to terminate the crawler

    Attributes
    ----------
    command_list : Dictionary
        dictionary for the commands
    pause : Threading.Event
        pause event to pause the crawler
    terminate : Threading.Event
        terminate event to terminate the crawler
    resume : Threading.Condition
        resume condition to continue the execution of the crawler

    """

    def __init__(self, pause, terminate, resume):
        self.command_list = {
            "pause": self.pause,
            "terminate": self.terminate,
            "resume": self.resume
        }
        self.pause = pause
        self.terminate = terminate
        self.resume = resume

    def pause(self):
        """Pauses the crawling process.

        When called, the crawling process pauses until the command for starting is called. If there is no active
        crawling process going on, the user is notified that there was no active crawling process.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """

        self.pause.set()
        Logger.log("state", "Pause is " + str(self.pause.is_set()))

    def terminate(self):
        """Terminates the crawling process.

        When called, the crawling process terminates and cannot be started from the CLI again. CLI is also shut down.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """

        self.terminate.set()
        Logger.log("state", "Terminate is " + str(self.terminate.is_set()))

    def resume(self):
        """Starts the crawling process.

        When called, the crawling process starts according to the workday schedule. If there is already an active
        crawling process going on, the user is notified there this is the case.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """

        # self.pause.clear()
        # Logger.log("state", "Pause is " + str(self.pause.is_set()))
        self.resume.acquire()
        self.resume.notify()
        self.resume.release()
        Logger.log("state", "Resuming the execution.")

    def skip_current_page(self):
        """Skips the current page during the crawling process.

        When called, the crawler will skip 'reading' the current page and move on to the next page, within the
        'moving to a next page' requirements.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return "Crawler skipped a page successfully"
        raise NotImplementedError()

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

        self.command_list[command_name]()
