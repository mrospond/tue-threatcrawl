from database.util import replace_values, is_binary_type, DocumentTraverser, DocumentReplacer
from database.querying import QueryBuilder
from database.errors import UnknownQueryTypeError, QueryContainsBinaryDataError, QueryError, DatabaseError
from database.common import QueryType, enums
from bson.objectid import ObjectId
from enum import Enum


class DataAPI:
    """DataAPI provides a simplified interface to the database, on top of the pymongo interface

    It's main feature is that it can work with binary data (files) inside the documents. Normally
    you would have to store a file separately and include a reference to the stored file
    in a document. When retrieving a document that contains a reference to a stored file,
    you would have to load that file manually.
    DataAPI does this automatically for you.

    Parameters
    ----------
    connection: DatabaseConnection
        A DatabaseConnection instance.

    Attributes
    ----------
    db: pymongo.database.Database
        This serves as the interface to the pymongo api.
    fs: gridfs.GridFs
        A GridFs instance, used to store and retrieve binary data.

    Methods
    -------
    remove_file(file_id)
        Removes the file with the given file id, if it exists.

    Notes
    -----
    This class does not actually contain the functions that will be used by the user. Those are
    defined in QueryBuilder (database.querying.query_builder.py).

    Suppose "api" is an instance of DataAPI. Then "api['users']" will return a QueryBuilder
    that can query the users collection. Collections names are not case sensitive, so "api['UseRS']"
    is valid as well.

    If the custom API does not provide some desired functionality, you can always resort to
    api.pymongo_api to directly query the database, bypassing the custom api. This of course means
    that you will have to store and retrieve any binary data manually whenever you have to work with
    binary data.
    """

    def __init__(self, connection):
        self.connection = connection
        self.db = connection.db
        self.fs = connection.fs

    @property
    def pymongo_api(self):
        """Exposes the pymongo API by returning the pymongo database object"""
        return self.db

    def __getitem__(self, key) -> QueryBuilder:
        """Creates and returns a QueryBuilder object

        Parameters
        ----------
        key: str
            The name of the collection to be queried.

        Returns
        -------
        QueryBuilder
            A QueryBuilder that can build queries for the provided collection.
        """
        # Use lower-case names to make collection-names case-insensitive to users of the API
        return QueryBuilder(self, key.lower())

    def execute_query(self, query):
        """Executes a query

        Parameters
        ----------
        query: Query
            A Query object containing all the information needed to execute a query.

        Returns
        -------
        any
            The query result, exact type and value depends on the query.

        Raises
        ------
        QueryError
            The query did not execute successfully.
        DatabaseError
            Base of all custom exceptions.
        """
        self.__pre_process(query)

        try:
            result = self.__execute_pymongo_query(query)
        except DatabaseError:
            # We do not want to catch custom errors
            raise
        except Exception as error:
            raise QueryError(query) from error

        return self.__post_process(query, result)

    def remove_file(self, file_id):
        """Removes a file with the given id, if it exists

        Parameters
        ----------
        file_id: str | ObjectId
            The id of the file to remove
        """
        if type(file_id) is str:
            file_id = ObjectId(file_id)

        self.fs.delete(file_id)

    def __pre_process(self, query):
        """Pre processes the query before executing it

        When a query contains binary data, this binary data will be stored
        separately and a reference will be inserted in the place of the
        binary data.
        It will also make sure that there is no binary data in e.g. a find
        or delete query, since querying on binary data is not supported (nor should it!)

        Parameters
        ----------
        query: Query
            The query to pre-process.
        """
        # Find and replace binary data with a reference to the uploaded file
        if query.type in [QueryType.INSERT, QueryType.UPDATE]:
            document = query.query if query.type is QueryType.INSERT else query.update
            DocumentTraverser(document).traverse(self.__replace_binary_data)

        if query.query is not None:
            query.query = self.__encode_enums(query.query)
        if query.update is not None:
            query.update = self.__encode_enums(query.update)

        # Ensure that the query does not contain binary data
        DocumentTraverser(query.query).traverse(self.__ensure_no_binary_data)

    def __encode_enums(self, document):
        """Replaces enum values with their database representation

        Parameters
        ----------
        document: dict
            Document that is about to get sent to the database.

        Returns
        -------
        dict
            The document with enum values that are safe
            to be stored in the database.
        """
        return DocumentReplacer(document).replace(self.__encode_enum_value)

    def __execute_pymongo_query(self, query):
        """Executes the given query using the pymongo api

        Parameters
        ----------
        query: Query
            The query to execute.

        Returns
        -------
        any
            The result of the query execution. Exact type can differ across query types.

        Raises
        ------
        UnknownQueryTypeError
            The type of the query is not recognized and the query can hence not be executed.
        """
        collection = self.db[query.collection]
        query_document = query.query

        if query.type == QueryType.INSERT:
            for key, value in dict(query_document).items():
                if value is None:
                    del query_document[key]
            result = collection.insert_one(query_document).inserted_id
        elif query.type == QueryType.FIND:
            if query.single_result:
                result = collection.find_one(query_document)
            else:
                result = list(collection.find(query_document))
        elif query.type == QueryType.UPDATE:
            if query.single_result:
                result = collection.update_one(query_document, query.update).matched_count
            else:
                # Note: this function does not have its return value wrapped in a wrapper class,
                # whereas all the others are. Hence the brackets. (inconsistency in pymongo)
                result = collection.update(query_document, query.update)['nModified']
        elif query.type == QueryType.DELETE:
            if query.single_result:
                # retrieve document
                document = collection.find_one(query_document)

                if document is None:
                    return 0

                result = collection.delete_one({'_id': document['_id']}).deleted_count
                self.__remove_referenced_files([document])
            else:
                documents = list(collection.find(query_document))
                ids = [document['_id'] for document in documents]
                result = collection.delete_many({'_id': {'$in': ids}}).deleted_count
                self.__remove_referenced_files(documents)

        elif query.type == QueryType.COUNT:
            result = collection.count_documents(query_document)
        else:
            raise UnknownQueryTypeError(query.type)

        return result

    def __post_process(self, query, result):
        """Post-processes a query and its result

        Post-processing mostly means replacing file-references for actual file contents
        and replacing reference to other documents with those documents. These replacements
        have to be specified by the user, so by default nothing gets replaced (mostly to prevent superfluous queries).

        Parameters
        ----------
        query: Query
            The query that was executed.

        result: any
            The result that was returned after the provided query was executed.

        Returns
        -------
        any
            `result`, but modified.
        """
        # We can only post-process (lists of) documents
        if type(result) not in [dict, list]:
            return result

        if query.single_result:
            result = [result]

        self.__replace_files(query, result)
        self.__replace_documents(query, result)

        result = [DocumentReplacer(document).replace(self.__decode_enum_value) for document in result]

        return result[0] if query.single_result else result

    def __encode_enum_value(self, value):
        """Encodes an enum value

        If `value` is an enum, it will be encoded and returned.
        If not, the unmodified value is returned.

        Parameters
        ----------
        value: any
            The enum to decode

        Returns
        -------
        any
            The encoded enum, or `value`
        """
        if isinstance(value, Enum):
            return {
                'enum_value': value.name,
                'enum_class': type(value).__name__
            }
        return value

    def __decode_enum_value(self, value):
        """Decodes an enum value into an instance of an enum

        If `value` can be decoded as an enum, the decoded value
        will be returned. Otherwise the original value is returned

        Parameters
        ----------
        value: any
            The value to decode

        Returns
        -------
        any
            The decoded enum, or `value`
        """
        if type(value) is dict and 'enum_value' in value and 'enum_class' in value:
            try:
                class_name = value['enum_class']
                class_member = value['enum_value']

                enum_class = getattr(enums, class_name)
                enum_instance = getattr(enum_class, class_member)
                return enum_instance
            except Exception:
                # If the conversion does not succeed, we leave it be.
                # Because then `value` might be a user-defined object, which we should preserve.
                pass

        return value

    def __remove_referenced_files(self, documents):
        """Removes all the files that are referenced in any of the documents

        Parameters
        ----------
        documents: list of dict
            A list of database documents
        """
        for document in documents:
            print(document)
            DocumentTraverser(document).traverse(self.__remove_file_by_id)

    def __remove_file_by_id(self, object, key, value):
        """Removes the file that has `value` as id, if it exists

        Parameters
        ----------
        object: any
            The object in which `value` located
        key: any
            The key that corresponds to `value`
        value: any
            The value that corresponds to `key`
        """
        if type(value) is ObjectId:
            self.fs.delete(value)

    def __replace_files(self, query, result):
        """Replaces references to files with the contents of the referenced file

        Parameters
        ----------
        query: Query
            The query that was executed.
        result: any
            The query result.
        """
        if query.file_replacements is not None:
            for path in query.file_replacements:
                path = path.split('.')
                for document in result:
                    replace_values(document, path, self.__retrieve_file_by_id)

    def __replace_documents(self, query, result):
        """Replaces references to documents with the referenced documents

        Parameters
        ----------
        query: Query
            The query that was executed.
        result: any
            The query result.
        """
        if query.replacements is not None:
            # replace the ObjectId's that are closest to the root of
            # the document first, to enable nested replacements
            query.replacements = sorted(query.replacements, key=lambda replacement: replacement['depth'])

            for replacement in query.replacements:
                path = replacement['path'].split('.')
                collection = replacement['collection']

                for document in result:
                    replace_values(
                        document,
                        path,
                        lambda id, collection=collection: self.__retrieve_document(id, collection))

    def __replace_binary_data(self, parent, index, value):
        """Replaces binary data with references

        When value is binary data, it will be separately
        stored as a file. A reference to that file will then
        be put in the place where the binary data was

        Parameters
        ----------
        parent: any
            The parent of `value`.
        index: int | str
            The index corresponding to `value`.
        value: any
            The value that should be replaced.

        Notes
        -----
        The following relation between the parameters holds:
            `parent[index] == value`
        """
        if is_binary_type(value):
            file_id = self.fs.put(value)
            parent[index] = file_id

    def __ensure_no_binary_data(self, parent, index, value):
        """Ensures that the value parameter is not binary data

        Parameters
        ----------
        parent: any
            The parent of `value` (not used).
        index: int | str
            The index corresponding to `value` (not used).
        value: any
            The value that should be replaced.

        Raises
        ------
        QueryContainsBinaryDataError
            `value` is binary data.

        Notes
        -----
        The following relation between the parameters holds:
            `parent[index] == value`
        """
        if is_binary_type(value):
            raise QueryContainsBinaryDataError()

    def __retrieve_file_by_id(self, id):
        """Given an id, return its corresponding file

        When `id` is a single id, the function will return one file. When it
        is a list of ids, it will return a list of files.

        Parameters
        ----------
        id: ObjectId | List of ObjectId
            The id of the file to be retrieved.

        Returns
        -------
        bytes | bytearray | list of (bytes | bytearray)
            The file(s) belonging to the given id(s).
        """
        if type(id) is list:
            return [self.fs.get(element).read() for element in id]
        else:
            return self.fs.get(id).read()

    def __retrieve_document(self, id, collection):
        """Retrieves a document with the specified id from the specified collection

        When `id` is a list, the return will also be a list. Works similar to
        __retrieve_file_by_id.

        Parameters
        ----------
        id: ObjectId | list of ObjectId
            The id of the document to retrieve.
        collection: str
            The collection that the document should be in.

        Returns
        -------
        dict | list of dict
            The document if found, otherwise None. A list of documents when parameter
            `id` is a list.
        """
        if type(id) is list:
            return [self.db[collection.lower()].find_one({'_id': element}) for element in id]
        else:
            return self.db[collection.lower()].find_one({'_id': id})
