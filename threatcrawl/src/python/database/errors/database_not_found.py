from .database_error import DatabaseError


class DatabaseNotFoundError(DatabaseError):
    """Raised when there is no database at the specified address

    Parameters
    ----------
    message: str, default="A database at the specified address could not be found"
        The error message
    """

    def __init__(self, message="A database at the specified address could not be found"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'
