"""File containing the XPath class."""
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver

from trainer.resource_identifier import ResourceIdentifier
from lxml import etree
from lxml.etree import tostring, Element
from utils import Logger


class XPath(ResourceIdentifier):
    """Class for XPath resource identifiers.

    XPath a query language for selecting nodes from an HTML document, can be used to navigate through elements and
    attributes in an HTML document.

    Attributes
    ----------
    x_path : str
        String representation of the XPath identifier.
    date_format : str
        The data format used for the element identified by this resource identifier.
        If this is not applicable, it has value None.
    """

    def __init__(self, x_path: str, date_format=None):
        """Initialize an XPath resource identifier.

        Parameters
        ----------
        x_path : str
            String representation of the XPath identifier.
        """
        super().__init__(date_format)
        if len(x_path) == 0:
            raise ValueError("x_path should be a non-empty string")
        self.x_path = x_path

    def get_elements(self, html: str) -> List[str]:
        """The HTML elements that are identified by this ResourceIdentifier.

        Find the HTML elements in the provided `html` that match this ResourceIdentifier.

        Parameters
        ----------
        html : str
            The HTML in which html elements are identified.

        Returns
        -------
        list of str
            A possibly empty list of HTML elements that match this ResourceIdentifier.
        """
        html_etree = self._get_elements_raw(html)
        html_list = [tostring(s, method='html', encoding=str).strip('\n\r\t ') for s in html_etree]
        return html_list

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

    def _get_elements_raw(self, html) -> List[Element]:
        """The HTML elements that are identified by this ResourceIdentifier.

        Parameters
        ----------
        html : str
            The HTML in which HTML elements are identified.

        Returns
        -------
        list of Element
            lxml elements that match this ResourceIdentifier.
        """
        # Convert str into html object
        html_obj = etree.HTML(html)

        if html_obj is None:
            Logger.log("trainer", "Parsing did not succeed! The HTML for which it failed is {}".format(html))
            return []
        else:
            # Get ElementUnicodeResult based on x_path
            return html_obj.xpath(self.x_path)

    def get_selenium_elements(self, driver: TorBrowserDriver) -> List[WebElement]:
        return driver.find_elements(By.XPATH, self.x_path)

    def to_database_format(self) -> dict:
        return {
            'identifier_XPATH': self.x_path
        }

    def __repr__(self) -> str:
        return self.x_path

    def __str__(self) -> str:
        return self.x_path
