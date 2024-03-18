"""File containing the AnalyzerMethod3 class."""
from typing import List, Optional

from selenium.webdriver.common.by import By
from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer
from enums import StructuralElement
from trainer.abstract_analyzer import AbstractAnalyzer
from trainer.html_element import HTMLElement
from trainer.xpath import XPath
from trainer.xpath_helper_functions import calculate_xpath, calculate_common_xpath


class AnalyzerMethod4(AbstractAnalyzer):
    """Class for constructing resource identifiers for HTML elements.

    The class uses the XPath properties of Selenium WebElements to identify them and to generate a ResourceIdentifier.
    This class doesn't make use of ignored_elements, therefore it is limited only to selected_elements and will fail in
    case of ignored_elements.
    """

    def __init__(self):
        pass

    def construct_identifier(self, page_html: str, selected_elements: List[HTMLElement],
                             ignored_elements: List[HTMLElement], structural_element: StructuralElement,
                             driver: TorBrowserDriver = None) -> Optional[DataContainer]:
        """The XPath identifier for a list of HTML elements on a web page.

        Construct the resource identifier for `html_elements`.

        Parameters
        ----------
        page_html : str
            Page from which `html_element` originates. No use of this in this method as it is embedded in the driver.
        selected_elements : list of HTMLElement
            The HTML elements for which a resource identifier is constructed.
        ignored_elements : list of HTMLElement
            The HTML elements that should not be selected by the identifier. This is not used, hence this class is
            limited to only selected elements.
        structural_element : StructuralElement
            The structural element that the `html_elements` represent, e.g. LoginButton. This is of no use.
        driver : TorBrowserDriver
            TorBrowserDriver necessary to identify the element on a page based on their XPath and to then calculate
            the correct identifier.

        Returns
        -------
        ResourceIdentifier or None
            The XPath or XPathExcept identifier with which all the `html_elements` and none of the `ignored_elements`
            are identified. Returns None if it was not possible to construct such an identifier.
        """
        identifier_or_none = None
        if isinstance(selected_elements, list):
            if len(selected_elements) == 1:
                # If the element clicked is only one, we take only the first!
                element = driver.find_elements(by=By.XPATH, value=selected_elements[0].x_path)[0]
                identifier_or_none = XPath(calculate_xpath(element, driver))
            elif len(selected_elements) > 1:
                xpaths = []
                for element in selected_elements:
                    current_element = driver.find_elements(by=By.XPATH, value=element.x_path)[0]
                    xpaths.append(calculate_xpath(current_element, driver))
                identifier_or_none = XPath(calculate_common_xpath(xpaths))
        if identifier_or_none.x_path == "//":
            identifier_or_none = None
        return identifier_or_none
