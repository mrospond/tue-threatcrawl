"""File containing the AnalyzerMethod1 class."""
from typing import List, Optional

import pymsgbox
from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer
from enums import StructuralElement
from trainer.html_element import HTMLElement
from trainer.xpath import XPath
from trainer.abstract_analyzer import AbstractAnalyzer


class XPathInjector(AbstractAnalyzer):
    """Class for constructing XPath identifiers using the provided XPath from the user."""

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
        answer = pymsgbox.prompt('Provide an XPath to identify ' + structural_element.name + ':', default='')
        if answer is not None and answer != '':
            return XPath(answer)
        else:
            return None
