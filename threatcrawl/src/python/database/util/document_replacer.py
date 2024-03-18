class DocumentReplacer:
    """Recursively traverses and transforms an object.

    DocumentReplacer traverse an object and calls the provided function for each
    value that it encounters. The return value of the function is used to replace the
    value. Using a void function will result in the document becoming None.

    Parameters
    ----------
    document: dictionary | list of any
        The document that shall be traversed and modified

    Attributes
    ----------
    document: dictionary | list of any
        A reference to the document parameter
    replace_function: Callable[any, any]
        The function that is called on each encountered value
    """
    def __init__(self, document):
        self.document = document
        self.replace_function = None

    def replace(self, replace_function=lambda x: x):
        """Initiates the traversal of the document

        Parameters
        ----------
        replace_function: Callable[any, any], default=lambda: x: x
            The function that will be called on each encountered value. It's return
            value will be used as a replacement of the original value.

        Returns
        -------
        dict
            The modified document
        """
        self.replace_function = replace_function
        return self.__replace(self.document)

    def __replace(self, document):
        """Traverses a document

        Upon execution, all values present in `document` will be iterated over,
        including nested values.

        Parameters
        ----------
        document: any
            The document to traverse

        Returns
        -------
        dict
            The modified document
        """
        if type(document) in [list, dict]:
            iterator = enumerate(document) if type(document) is list else document.items()

            for key, value in iterator:
                document[key] = self.__replace(value)

        return self.replace_function(document)
