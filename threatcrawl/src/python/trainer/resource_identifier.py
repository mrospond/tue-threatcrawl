"""File containing the ResourceIdentifier, XPath and HTMLClass classes."""
from abc import abstractmethod
# from enums.navigational_element import NavigationalElement
# from enums.input_element import InputElement
# from enums.data_element import DataElement
from typing import List

from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer


class ResourceIdentifier(DataContainer):
    """Abstract class for resource identifiers.

    Attributes
    ----------
    date_format : str or None
        The data format used for the element identified by this resource identifier.
        If this is not applicable, it has value None.
    """

    @abstractmethod
    def __init__(self, date_format=None):
        """The abstract class cannot be instantiated."""
        self.date_format = date_format

    @abstractmethod
    def get_elements(self, html: str) -> List[str]:
        """The HTML elements that are identified by this ResourceIdentifier.

        Find the HTML elements in the provided `html` that match this ResourceIdentifier.

        Parameters
        ----------
        html : str
            The HTML in which HTML elements are identified.

        Returns
        -------
        list of str
            A possibly empty list of HTML elements that match this ResourceIdentifier.
        """
        pass

    @abstractmethod
    def get_selenium_elements(self, driver: TorBrowserDriver):
        """The HTML elements that are identified by this ResourceIdentifier.

        Find the required WebElement from the page.

        Parameters
        ----------
        driver : TorBrowserDriver
            SeleniumTOR driver.

        Returns
        -------
        list of allowed WebElement
        """
        pass

    def get_number_of_elements(self, html: str) -> int:
        """The number of HTML elements that are identified by this ResourceIdentifier.

        Parameters
        ----------
        html : str
            The HTML in which HTML elements are identified.

        Returns
        -------
        int
            The number of HTML elements that are identifier by this ResourceIdentifier.
        """
        return len(self.get_elements(html))
