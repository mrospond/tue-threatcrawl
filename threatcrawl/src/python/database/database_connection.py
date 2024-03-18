from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from database.util import SchemaConverter
from database.schemas import schemas
from database.errors import DatabaseNotFoundError, DatabaseConnectionError, SchemaConversionError
from gridfs import GridFS


class DatabaseConnection:
    """Class that connects to a database instance.

    DatabaseConnection connects to a database instance and creates
    all the collections with validation schemas as defined in database.schemas.

    Parameters
    ----------
    username: str
        The name of the database user.
    password: str
        The password of the database user.
    host: str
        Hostname or IP of the database's address.
    port: str, default='27017'
        The port on which the database instance is exposed.
    auth_database: str, default='admin
        The database used to authenticate the database user.
    connection_timeout_ms: int, default=30000
        The connection timeout in milliseconds. If there is no connection after this amount of time,
        a timeout error is raised.

    Attributes
    ----------
    __client: MongoClient
        The pymongo client interface to the database.
    db: Database
        The pymongo database interface, linked to the database that is used.
    fs: GridFS
        A GridFS instance connected to the database that is used. Can be used to store and retrieve files (binary data).

    Raises
    ------
    DatabaseNotFoundError
        There is no database at the specified address
    DatabaseConnectionError
        There is a database instance at the specified address, but a connection could not be made
    """
    def __init__(self, username, password, host, port='27017', auth_database='admin', connection_timeout_ms=30000):
        connection_string = f'mongodb://{username}:{password}@{host}:{port}/{auth_database}'
        self.__client = MongoClient(connection_string, serverSelectionTimeoutMS=connection_timeout_ms)
        self.__ensure_connected()
        self.__initialize()

    def __ensure_connected(self):
        """Ensures a working database connection

        Ensures that there is a working connection to the database instance and will raise an exception if
        that is not the case.

        Raises
        ------
        DatabaseNotFoundError
            There is no database at the specified address
        DatabaseConnectionError
            There is a database instance at the specified address, but a connection could not be made
        """
        try:
            self.__client.server_info()
        except ServerSelectionTimeoutError as error:
            raise DatabaseNotFoundError() from error
        except Exception as error:
            raise DatabaseConnectionError() from error

    def __initialize(self):
        """Initializes the database if it is not already initialized"""
        collection_names = [schema['collection'].lower() for schema in schemas]

        self.db = self.__client.THREATcrawl
        self.fs = GridFS(self.db)
        self.__ensure_collections_created(collection_names)
        self.__set_schemas(schemas)

    def __ensure_collections_created(self, collections):
        """Ensures that the provided collections exist

        Parameters
        ----------
        collections: list of str
            A list with collections names that should exist
        """
        existing_collections = self.db.list_collection_names()

        for collection in collections:
            if collection not in existing_collections:
                self.db.create_collection(collection)

    def __set_schemas(self, schemas):
        """Sets the validation schemas on the collections.

        A collection can have a validation schema, containing a list of fields and their types. These
        are used to validate the data in the collections upon document inserts and updates.

        Parameters
        ----------
        schemas: list of dict
            A list of validation schemas (like the schemas in the database.schemas module)

        Raises
        ------
        SchemaConversionError
            A schema could not be converted to the type that MongoDB expects ($jsonSchema)
        """
        for schema in schemas:
            collection_name = schema['collection'].lower()
            try:
                json_schema = SchemaConverter(schema).get_json_schema()
            except Exception as error:
                raise SchemaConversionError(schema) from error

            self.db.command({
                'collMod': collection_name,
                'validator': {
                    '$jsonSchema': json_schema
                }
            })
