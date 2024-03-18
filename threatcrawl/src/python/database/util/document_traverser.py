class DocumentTraverser:
    """Recursively traverses an object.

    DocumentTraverse traverses an object and calls the provided function for each
    value that it encounters. The function will be called with the three arguments:
    the parent of the value (a dictionary or a list), the index/key of the value,
    and the value itself. (parent[index] == value)

    Dictionaries and lists will be traversed, other types (e.g. class instances) will be
    classified as a value. This is enough for JSON-like documents to be traversed.

    Parameters
    ----------
    document: dictionary | list of any
        The document that shall be traversed

    Attributes
    ----------
    document: dictionary | list of any
        A reference to the document parameter
    traverse_function: Callable[[any, any, any], None]
        The function that is called on each encountered value as described in the summary
    """
    def __init__(self, document):
        self.document = document
        self.traverse_function = None

    def traverse(self, traverse_function=lambda x, y, z: None):
        """Initiates the traversal of the document

        Parameters
        ----------
        traverse_function: Callable[[any, any, any], None], default=lambda: x,y,z: None
            The function that will be called on each encountered value
        """
        self.traverse_function = traverse_function
        self.__traverse(self.document)

    def __traverse(self, document):
        """Traverses a document

        Upon execution, all values present in `document` will be iterated over,
        including nested values.

        Parameters
        ----------
        document: any
            The document to traverse
        """
        if type(document) not in [dict, list]:
            return

        iterator = enumerate(document) if type(document) is list else document.items()

        for key, value in iterator:
            self.traverse_function(document, key, value)
            self.__traverse(value)
