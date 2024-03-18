"""File containing the XPath class."""
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver

from trainer.xpath import XPath
from trainer.resource_identifier import ResourceIdentifier


class XPathExcept(ResourceIdentifier):
    """Class for XPath resource identifiers.

    XPath a query language for selecting nodes from an HTML document, can be used to navigate through elements and
    attributes in an HTML document.

    Attributes
    ----------
    x_path_use : XPath
        String representation of the XPath identifier, identifying the wanted elements.
    x_path_remove: XPath
        String representation of the XPath identifier, identifying the unwanted elements.
    date_format : str
        The data format used for the element identified by this resource identifier.
        If this is not applicable, it has value None.
    """

    def __init__(self, x_path_use: XPath, x_path_remove: XPath, date_format=None):
        """Initialize an XPath resource identifier.

        Parameters
        ----------
        x_path_use : XPath
            String representation of the XPath identifier, identifying the wanted elements.
        x_path_remove: XPath
            String representation of the XPath identifier, identifying the unwanted elements.
        """
        super().__init__(date_format)
        self.x_path_use = x_path_use
        self.x_path_remove = x_path_remove
        assert type(x_path_use) == XPath
        assert type(x_path_remove) == XPath

    def get_elements(self, html_str) -> List[str]:
        wanted_elements = self.x_path_use.get_elements(html_str)
        unwanted_elements = self.x_path_remove.get_elements(html_str)

        return list(set(wanted_elements) - set(unwanted_elements))

    def to_database_format(self) -> dict:
        return {
            'identifier_HTML': self.x_path
        }

    def get_selenium_elements(self, driver: TorBrowserDriver) -> List[WebElement]:
        allowed_elements = driver.find_elements(By.XPATH, self.x_path_use.x_path)
        disallowed_elements = driver.find_elements(By.XPATH, self.x_path_remove.x_path)
        disallowed_ids = []
        for element in disallowed_elements:
            disallowed_ids.append(element.id)
        result = [x for x in allowed_elements if x.id not in disallowed_ids]
        return result

    def __repr__(self) -> str:
        return f"Use: {self.x_path_use}; Remove: {self.x_path_remove}"
