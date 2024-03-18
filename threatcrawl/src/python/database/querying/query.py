class Query:
    """Query describes a database query

    Parameters
    ----------
    collection: str, default=None
        The collection that the query targets
    type: int, default=None
        The type of query
    query: dict, default=None
        The filter of the query. This part is used to match documents
    update: dict, default=None
        An update document that contains what should be updated in the documents
        that are matched with the query. Can naturally only be used in an update query.
    single_result: bool, default=False
        Specifies if the query shall return a single document or a list of documents
    file_replacements: list of str, default=None
        A list of paths to file references. Each file reference on these paths will
        be replaced with the contents of the file that it points to.
    replacements: list of dict, default=None
        Similar to file_replacements, but for references to other documents instead
        of files. Each dictionary in the list shall have the following three properties:
            - path: str
                path to a document reference
            - collection: str
                name of the collection that the referenced document is in
            - depth: str
                The depth of the path. For example, "root.posts.author" has a depth of 2
                and just "root" has a depth of 0. (calculated with path.count('.'))
    """

    def __init__(self, collection: str = None, type: int = None, query: dict = None, update: dict = None,
                 single_result: bool = False, file_replacements: list = None, replacements: list = None):
        self.collection = collection
        self.type = type
        self.query = query
        self.update = update
        self.single_result = single_result
        self.file_replacements = file_replacements
        self.replacements = replacements
