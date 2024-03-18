from bson.objectid import ObjectId
from .query import Query
from database.common import QueryType


class QueryBuilder:
    """QueryBuilder provides an interface for constructing queries

    QueryBuilder let's you build a query easily, without having to construct
    a Query object manually. Each method returns self, so you can chain method
    calls. When the query is fully constructed, the exec() method must be called
    to execute the query.

    MongoDB uses query documents [1] and update documents [2].

    Parameters
    ----------
    api_instance: DataAPI
        The api instance that instantiated the QueryBuilder object.
    collection_name: str
        Name of the collection that the query will run on.

    Attributes
    ----------
    api_instance: DataAPI
        The api instance that instantiated the QueryBuilder object.
    query: Query
        The query that the QueryBuilder is building

    References
    ----------
    [1] https://docs.mongodb.com/manual/tutorial/query-documents/
    [2] https://docs.mongodb.com/manual/tutorial/update-documents/
    """
    def __init__(self, api_instance, collection_name):
        self.api_instance = api_instance
        self.query = Query()
        self.query.collection = collection_name

    def exec(self):
        """Executes the query that has been built and returns the result"""
        return self.api_instance.execute_query(self.query)

    def insert(self, document):
        """Inserts a new document in the collection

        Parameters
        ----------
        document: dict
            The document to be inserted

        Returns
        -------
        The QueryBuilder instance
        """
        self.query.type = QueryType.INSERT
        self.query.query = document
        return self

    def find(self, query={}):
        """Queries a collection

        Queries a collection and returns all the documents that match the query.

        Parameters
        ----------
        query: dict, default={}
            A mongodb query document

        Returns
        -------
        The QueryBuilder instance
        """
        self.query.type = QueryType.FIND
        self.query.query = query
        return self

    def find_one(self, query={}):
        """Queries a collection

        Queries a collection and returns the first document that matches the query.

        Parameters
        ----------
        query: dict, default={}
            A mongodb query document

        Returns
        -------
        The QueryBuilder instance
        """
        self.find(query)
        self.query.single_result = True
        return self

    def find_by_id(self, id):
        """Queries a collection

        Queries a collection with an id and returns the document if it exists

        Parameters
        ----------
        id: str | ObjectId
            The id of the document to find

        Returns
        -------
        The QueryBuilder instance
        """
        if type(id) is str:
            id = ObjectId(id)
        self.find_one({'_id': id})
        return self

    def update(self, query, update):
        """Updates documents in a collection

        Updates all documents that are matched by the query.

        Parameters
        ----------
        query: dict
            A mongodb query document
        update: dict
            A mongodb update document

        Returns
        -------
        The QueryBuilder instance

        Notes
        -----
        IMPORTANT: If you overwrite a (reference to a ) file, you 
        must delete the overwritten file manually. You can delete a file by 
        calling remove_file(id) on a DataAPI instance.
        """
        self.query.type = QueryType.UPDATE
        self.query.query = query
        self.query.update = update
        return self

    def update_one(self, query, update):
        """Updates a document in a collection

        Updates the first document that matches the query.

        Parameters
        ----------
        query: dict
            A mongodb query document
        update: dict
            A mongodb update document

        Returns
        -------
        The QueryBuilder instance

        Notes
        -----
        IMPORTANT: If you overwrite a (reference to a ) file, you 
        must delete the overwritten file manually. You can delete a file by
        calling remove_file(id) on a DataAPI instance.
        """
        self.update(query, update)
        self.query.single_result = True
        return self

    def update_by_id(self, id, update):
        """Updates a document in a collection

        Updates the document with the specified id

        Parameters
        ----------
        id: str | ObjectId
            The id of the document to update
        update: dict
            A mongodb update document

        Returns
        -------
        The QueryBuilder instance

        Notes
        -----
        IMPORTANT: If you overwrite a (reference to a ) file, you 
        must delete it the overwritten file manually. You can delete a file by
        calling remove_file(id) on a DataAPI instance.
        """
        if type(id) is str:
            id = ObjectId(id)
        self.update_one({'_id': id}, update)
        return self

    def delete(self, query):
        """Deletes documents from a collection

        Deletes all the documents that match the query.

        Parameters
        ----------
        query: dict
            A mongodb query document

        Returns
        -------
        The QueryBuilder instance
        """
        self.query.type = QueryType.DELETE
        self.query.query = query
        return self

    def delete_one(self, query):
        """Deletes a document from a collection

        Deletes the first document that matches the query.

        Parameters
        ----------
        query: dict
            A mongodb query document

        Returns
        -------
        The QueryBuilder instance
        """
        self.delete(query)
        self.query.single_result = True
        return self

    def delete_by_id(self, id):
        """Deletes a document from a collection

        Deletes the document with the specified id.

        Parameters
        ----------
        id: str | ObjectId
            The id of the document to delete

        Returns
        -------
        The QueryBuilder instance
        """
        if type(id) is str:
            id = ObjectId(id)
        self.delete_one({'_id': id})
        return self

    def count_documents(self, filter={}):
        """Counts the documents that match the filter

        Parameters
        ----------
        filter: dict, default={}
            A mongodb query document

        Returns
        -------
        The QueryBuilder instance
        """
        self.query.query = filter
        self.query.type = QueryType.COUNT
        return self

    def include(self, path, collection):
        """Replaces a document reference

        Replaces the document reference(s) located at path
        with the document that it references. When the path
        points to an array of document references, all references
        will be replaced.

        Parameters
        ----------
        path: str
            The path to the document reference(s).
        collection: str
            The name of the collection that the document is in.

        Returns
        -------
        The QueryBuilder instance
        """
        if self.query.replacements is None:
            self.query.replacements = []

        self.query.replacements.append({'path': path, 'collection': collection, 'depth': path.count('.')})
        return self

    def include_files(self, paths):
        """Replaces file references

        Same as include_file(), but takes multiple paths
        instead of a single path.

        Parameters
        ----------
        paths: list of str
            List of paths to file references

        Returns
        -------
        The QueryBuilder instance

        See also
        --------
        include_file(path)
        """
        if self.query.file_replacements is None:
            self.query.file_replacements = []

        self.query.file_replacements.extend(paths)
        return self

    def include_file(self, path):
        """Replaces a file reference

        Replaces the file reference(s) located at path
        with the file that it references. When the path
        points to an array of file references, all references
        will be replaced.

        Parameters
        ----------
        path: str
            The path to the file reference(s).

        Returns
        -------
        The QueryBuilder instance
        """
        return self.include_files([path])
