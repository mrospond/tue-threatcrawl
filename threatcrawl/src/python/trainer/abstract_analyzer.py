"""File containing the AbstractAnalyzer class."""
from abc import ABC, abstractmethod
from typing import List, Optional

from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer
from enums import StructuralElement
from trainer.html_element import HTMLElement


class AbstractAnalyzer(ABC):
    """Abstract class for constructing resource identifiers for html elements."""

    @abstractmethod
    def __init__(self):
        """The abstract class cannot be instantiated; implementations can initialize necessary variables."""
        pass

    @abstractmethod
    def construct_identifier(self, page_html: str, selected_elements: List[HTMLElement],
                             ignored_elements: List[HTMLElement], structural_element: StructuralElement,
                             driver: TorBrowserDriver = None) -> Optional[DataContainer]:
        """The identifier for a list of HTML elements on a web page.

        Construct the resource identifier for `html_elements`.

        Parameters
        ----------
        page_html : str
            Page from which `html_element` originates.
        selected_elements : List[HTMLElement]
            The HTML elements for which a resource identifier is constructed.
        ignored_elements : List[HTMLElement]
            The HTML elements that should not be selected by the identifier.
        structural_element : StructuralElement
            The structural element that the `html_elements` represent, e.g. LoginButton.
        driver : TorBrowserDriver
            The TorBrowserDriver necessary only for one AnalyzerMethod using Selenium to identify the elements.
            Overloading is not possible, and Multidispatching is not recommended in multithreaded programs, hence this
            questionable solution.

        Returns
        -------
        ResourceIdentifier or None
            The resource identifier with which all the `html_elements` and none of the `ignored_elements`
            are identified. Returns None if it was not possible to construct such an identifier.
        """
        pass
