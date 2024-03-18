"""CLI class for the CLI module"""

from cli.captcha_command import CaptchaCommand
from cli.config_command import ConfigCommand
from cli.crawl_command import CrawlCommand
from cli.export_command import ExportCommand
from cli.keyword_command import KeywordCommand
from cli.stat_command import StatCommand
from crawler.crawler_time_controller import CrawlerTimeController
from utils import Logger


class CLI:
    """CLI class for the CLI module.

    The CLI class allows for the user to give commands to the CLI.
    It mainly reads the users input and forwards the commands to the
    command class.


    crawl_command : CrawlCommand
        Command class for all crawl commands
    config_command : ConfigCommand
        Command class for all configuration commands
    export_command : ExportCommand
        Command class for all export commands
    keyword_command : KeywordCommand
        Command class for all keyword commands
    stat_command : StatCommand
        Command class for all statistics commands
    command_list : Dictionary
        Dictionary containing all commands with its specific class

    """

    def __init__(self, commands, craw_time_contr: CrawlerTimeController):
        self.__craw_time_contr = craw_time_contr
        self.crawl_command = CrawlCommand(commands.pause, commands.terminate, commands.resume)
        self.captcha_command = CaptchaCommand(commands.solved)
        self.config_command = ConfigCommand()  # Not used, here for the future
        self.export_command = ExportCommand()  # Not used, here for the future
        self.keyword_command = KeywordCommand()  # Not used, here for the future
        self.stat_command = StatCommand()  # Not used, here for the future
        self.command_list = {
            "pause": self.crawl_command.execute,
            "terminate": self.crawl_command.execute,
            "resume": self.crawl_command.execute,
            "solved": self.captcha_command.execute
        }

    def notify_bad_formatted_page(self):
        """Notifies the user that a visited page is badly formatted

        If the crawler encounters a badly formatted page, the CLI notifies the user that this happened.
        """
        Logger.log("warning", "Badly formatted page encountered")

    def execute_command(self):
        """Reads user input and executes the correct command if the command exists.

        Reads input from user and checks which to which specialised command class the command belongs. It then passes
         he command to the specialised command class. If the parameters are incorrect or the command does not exist, it
         will notify the user that the command was invalid or that the parameters were incorrect.

        Raises
        ------
        NonExistentCommandException
            The given command name could not be located in the given command type.
        BadArgumentException
            The given argument for the given command is invalid.
        CommandFailureException
            The given command could not be executed.
        """

        # This variable is used to keep the terminal open for input until the terminate command is called
        on: bool = True

        # Keep the terminal open and process input until the CLI is terminated
        while on:

            # Read the input and split on spaces
            a = input()
            data = a.split(" ")

            # If only one word is given (a command), add `None` to the split
            if len(data) == 1:
                data.append(None)

            # Stop the loop if the terminate command is called
            if data[0] == "terminate":
                on = False

            if data[0] in self.command_list:
                self.command_list[data[0]](data[0], data[1])

            # The command does not exist, so notify the user
            else:
                Logger.log("error", "Command not found")
