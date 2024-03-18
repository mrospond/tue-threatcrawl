import json
from .database_error import DatabaseError


class SchemaConversionError(DatabaseError):
    """Raised when a validation scheme can not be converted to a $jsonSchema

    Parameters
    ----------
    schema: dict
        The schema that could not be converted
    message: str, default="Could not convert the schema to its $jsonSchema equivalent"
        The error message
    """

    def __init__(self, schema, message="Could not convert the schema to its $jsonSchema equivalent"):
        self.schema = schema
        self.message = message
        super().__init__(message)

    def __str__(self):
        return f'{self.message}.\n\nSchema: {json.dumps(self.schema, indent=4)}'
