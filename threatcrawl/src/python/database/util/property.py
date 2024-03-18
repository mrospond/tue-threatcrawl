from inspect import isclass
from enum import Enum


class Property:
    """Intermediate representation of a document property

    The validation schemas of collections in the database consist of
    properties and their types, along with some additional information.
    This class describes a single property of such a document, which is essentially
    analogues to a column in a relational database.

    Parameters
    ----------
    name: str
        The name of the property
    type: str
        The type of the property (database.common.datatypes.py contains a collection of possible types).
    is_array: bool, default=False
        Boolean indicating whether the value belonging to the property is an array.
    required: bool, default=True
        Boolean indicating whether the property must be present in a document.
    description: str, default=None
        A description of the property
    properties: list of Property, default=None
        When the type of the property is an object, you must define
        the properties that these objects must have using this list.

    Attributes
    ----------
    Exactly as parameters, Property is just a data-container

    Notes
    -----
    This class is used as an intermdiate representation of a property,
    which is helpful when converting schemas to $jsonSchemas.
    """
    def __init__(self, name, type, is_array=False, required=True, description=None, properties=None):
        self.name = name
        self.type = type
        self.is_array = is_array
        self.required = required
        self.description = description
        self.properties = properties

    @property
    def is_enum(self):
        """Returns whether the property type is an enumeration"""
        return isclass(self.type) and issubclass(self.type, Enum)
