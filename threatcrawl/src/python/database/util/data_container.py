from abc import ABC, abstractmethod


class DataContainer(ABC):
    """An abstract class for classes that contain database data

    If a class contains data the can be saved to the database it is
    useful to have a function that converts the data into a format
    that the database can store (dictionary). This abstract class
    enforces such a method on its subclasses.
    """

    @abstractmethod
    def to_database_format(self):
        """Returns the contents of the instance in a dictionary

        If a class contains data that can be saved to the database, this function
        will return that data in a format that can be saved to the database.

        Returns
        -------
        dict
            dictionary with data from self.
        """
        pass
