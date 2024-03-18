"""File containing the HTMLClass class."""
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver

from trainer.resource_identifier import ResourceIdentifier
from bs4 import BeautifulSoup
from bs4.element import ResultSet


class HTMLClass(ResourceIdentifier):
    """Class for HTML class resource identifiers.

    This ResourceIdentifier identifies HTML elements based on their HTML classes.

    Attributes
    ----------
    html_classes : list of str
        Non-empty list of HTML classes for identifying HTML elements.
    date_format : str
        The data format used for the element identified by this resource identifier.
        If this is not applicable, it has value None.
    """

    def __init__(self, html_classes: List[str], date_format=None):
        """Initialize an HTML class resource identifier.

        Parameters
        ----------
        html_classes : list of str
            Non-empty list of HTML classes for identifying HTML elements.

        Raises
        ------
        ValueError
            If the provided list of classes is empty.
        """
        super().__init__(date_format)
        if len(html_classes) == 0:
            raise ValueError("html_classes should be a non-empty list")
        self.html_classes = html_classes

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
        result_set = self._get_elements_raw(html)
        return [str(tag) for tag in result_set]

    def get_selenium_elements(self, driver: TorBrowserDriver) -> List[WebElement]:
        return driver.find_elements(By.XPATH, self.x_path)

    def _get_elements_raw(self, html) -> ResultSet:
        """The HTML elements that are identified by this ResourceIdentifier.

        Find the HTML elements in the provided `html` that match this ResourceIdentifier.

        Parameters
        ----------
        html : str
            The HTML in which HTML elements are identified.

        Returns
        -------
        ResultSet
            BeautifulSoup tags that match this ResourceIdentifier.
        """
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all(None, {'class': self.html_classes})

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
        return len(self._get_elements_raw(html))

    def to_database_format(self) -> dict:
        return {
            'identifier_HTML': self.html_classes
        }
