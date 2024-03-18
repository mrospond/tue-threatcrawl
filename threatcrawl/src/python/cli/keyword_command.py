"""KeywordCommand class for the CLI module"""
from typing import Union, Optional

from cli.command import Command


class KeywordCommand(Command):
    """KeywordCommand class for the CLI module.

    The KeyWordCommand class hosts the possibility to execute commands related to keywords.
    This class contains the commands for adding, removing and showing relevant keywords and blacklisted keywords.

    """

    # This is a should
    def add_relevant_keyword(self, keyword):
        """Adds `keyword` to the list of relevant keywords.

        If `keyword` already exists in the list of relevant keywords, `keyword` will not be added and the user is
        notified that `keyword` was already in the list of relevant keywords.

        Parameters
        ----------
        keyword : str
            The keyword to add to the list of relevant keywords.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return keyword + " has been added to relevant keywords successfully"
        raise NotImplementedError()

    # This is a should
    def add_blacklisted_keyword(self, keyword):
        """Adds `keyword` to the list of blacklisted keywords.

        If `keyword` already exists in the list of blacklisted keywords, `keyword` will not be added and the user is
        notified that `keyword` was already in the list of blacklisted keywords.

        Parameters
        ----------
        keyword : str
            The keyword to add to the list of blacklisted keywords.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return keyword + " has been added to blacklisted keywords successfully"
        raise NotImplementedError()

    # This is a should
    def remove_relevant_keyword(self, keyword):
        """Removes `keyword` from the list of relevant keywords.

        If `keyword` didn't exist in the list of relevant keywords, the user is notified that `keyword` was already
        not in the list of relevant keywords.

        Parameters
        ----------
        keyword : str
            The keyword to remove from the list of relevant keywords.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return keyword + " has been removed from relevant keywords successfully"
        raise NotImplementedError()

    # This is a should
    def remove_blacklisted_keyword(self, keyword):
        """Removes `keyword` from the list of blacklisted keywords.

        If `keyword` didn't exist in the list of blacklisted keywords, the user is notified that `keyword` was already
        not in the list of blacklisted keywords.

        Parameters
        ----------
        keyword : str
            The keyword to remove from the list of blacklisted keywords.

        Raises
        ------
        BadArgumentException
            The given argument is invalid.
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        # return keyword + " has been removed from blacklisted keywords successfully"
        raise NotImplementedError()

    def show_relevant_keywords(self):
        """Shows the list of relevant keywords.

        Returns
        -------
        keywords: str
            The list of relevant keywords.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        return "List of relevant keywords shown successfully"

    def show_blacklisted_keywords(self):
        """Shows the list of blacklisted keywords.

        Returns
        -------
        keywords: str
            The list of blacklisted keywords.

        Raises
        ------
        CommandFailureException
            The given command could not be executed.
        """
        # TODO actual implementation
        return "List of blacklisted keywords shown successfully"

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
