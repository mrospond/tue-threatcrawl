from .database_error import DatabaseError
from database.util import pretty_print


class QueryError(DatabaseError):
    """A general query error. Raised when a query is not successfully executed and no more specific exception is available

    Parameters
    ----------
    query: Query
        The query that failed to execute
    message: str, default="Query could not be executed because an error occurred"
        The error message
    """

    def __init__(self, query, message="Query could not be executed because an error occurred"):
        self.query = query
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}.\n\nQuery: {pretty_print(self.query)}'
