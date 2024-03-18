from .database_error import DatabaseError


class UnknownQueryTypeError(DatabaseError):
    """Raised whenever a query is of an unknown type

    Parameters
    ----------
    query_type: int
        The query type that triggered the exception
    message: str, default="Cannot execute query because the query type is unknown"
        The error message
    """

    def __init__(self, query_type, message="Cannot execute query because the query type is unknown"):
        self.query_type = query_type
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f'{self.message}. Query type: {self.query_type}'
