from .database_error import DatabaseError


class DatabaseConnectionError(DatabaseError):
    """Raised when there is a database at the specified address, but during connecting an error occurs

    Parameters
    ----------
    message: str, default="There was an error during the setup of the database connection"
        The error message
    """

    def __init__(self, message="There was an error during the setup of the database connection"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}'
