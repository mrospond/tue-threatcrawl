from database.common import DataType
from .property import Property


class SchemaConverter:
    """SchemaConverter converts schemas to $jsonSchemas.

    Schemas are used to describe the structure of a collection in the database.
    MongoDB uses the $jsonSchema format for this, but because it can be confusing
    to use sometimes, we use a simplified version of schemas to describe collections.
    This class can take such a simplified schema and convert it into the format that
    MongoDB expects.

    Parameters
    ----------
    schema: dict
        The simplified version of the $jsonSchema format

    Attributes
    ----------
    schema: dict
        The schema provided in the constructor
    json_schema: dict
        The schema converted into $jsonSchema format

    Methods
    -------
    get_json_schema: dict
        Returns the $jsonSchema representation of the schema. If it does not exist already,
        it will be created first.
    """
    def __init__(self, schema):
        self.schema = schema
        self.json_schema = None

    def __convert_enum(self, property):
        """Converts a single enum property object

        Enums need additional information stored with them (the enum class name)
        for them to be decodeable upon data retrieval. This method creates a
        $jsonSchema structure that incorporates that.

        Parameters
        ----------
        property: Property
            The (enum) property. `property.is_enum` shall hold.

        Returns
        -------
        dict
            A $jsonSchema for the provided property.
        """
        if not property.is_enum:
            raise ValueError('SchemaConverter.__convert_enum was called with a property that is not an enum')

        return {
            'bsonType': DataType.OBJECT,
            'properties': {
                'enum_value': {
                    'enum': [element.name for element in property.type]
                },
                'enum_class': {
                    'bsonType': DataType.STRING
                }
            },
            'required': ['enum_value', 'enum_class']
        }

    def __convert_property(self, property):
        """Converts a single property object to $jsonSchema format

        Parameters
        ----------
        property: Property
            The property to convert

        Returns
        -------
        dict
            The equivalent $jsonSchema representation of the property parameter
        """
        value = {}

        if property.type is DataType.OBJECT:
            value = self.__create_json_schema(property.properties)
        elif property.is_enum:
            value = self.__convert_enum(property)
        else:
            value['bsonType'] = property.type

        if property.is_array:
            value = {
                'bsonType': DataType.ARRAY,
                'items': value
            }

        if property.description is not None:
            value['description'] = property.description

        return value

    def __create_json_schema(self, properties):
        """Returns a $jsonSchema built from a list of Property objects

        Parameters
        ----------
        properties: list of Property
            A list of properties that define a validation schema.

        Returns
        -------
            A $jsonSchema representation of the provided list of properties.
        """
        json_schema = {
            'bsonType': DataType.OBJECT,
            'properties': {property.name: self.__convert_property(property) for property in properties},
            'required': [p.name for p in properties if p.required]
        }

        # MongoDB does not accept empty required arrays :)
        if len(json_schema['required']) == 0:
            del json_schema['required']

        return json_schema

    def __extract_properties(self, schema_properties):
        """Converts a simplified validation schema to a list of Property objects

        Parameters
        ----------
        schema_properties: dict
            A simplified validation schema.

        Returns
        -------
        list of Property
            A list of property objects that contains all the information available
            in schema_properties.
        """
        properties = []
        for property, value in schema_properties.items():
            property_object = Property(
                property,
                value['type'],
                value['isArray'] if 'isArray' in value else False,
                value['required'] if 'required' in value else True,
                value['description'] if 'description' in value else None,
                value['properties'] if 'properties' in value else None)

            if property_object.properties is not None:
                property_object.properties = self.__extract_properties(property_object.properties)

            properties.append(property_object)

        return properties

    def __convert(self):
        """Converts the schema into the $jsonSchema format"""
        properties = self.__extract_properties(self.schema['properties'])
        self.json_schema = self.__create_json_schema(properties)

    def get_json_schema(self):
        """Returns the schema in $jsonSchema format

        Returns
        -------
        dict
            A $jsonSchema equivalent to the provided schema
        """
        if self.json_schema is None:
            self.__convert()

        return self.json_schema
