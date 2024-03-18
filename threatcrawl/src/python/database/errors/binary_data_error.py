from .database_error import DatabaseError


class QueryContainsBinaryDataError(DatabaseError):
    """Raised when a query document contains binary data (e.g. a file)"""
    pass
