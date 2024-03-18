"""File containing the AnalyzerMethod1 class."""
from typing import List, Optional

from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer
from enums import StructuralElement
from trainer.abstract_analyzer import AbstractAnalyzer
from bs4 import BeautifulSoup

from trainer.html_element import HTMLElement
from trainer.xpath import XPath


class AnalyzerMethod1(AbstractAnalyzer):
    """Class for constructing resource identifiers for HTML elements with implemented method 1."""

    def __init__(self):
        pass

    def construct_identifier(self, page_html: str, selected_elements: List[HTMLElement],
                             ignored_elements: List[HTMLElement], structural_element: StructuralElement,
                             driver: TorBrowserDriver = None) -> Optional[DataContainer]:
        """The HTMLClass identifier for a list of HTML elements on a web page, if possible.

        Construct the resource identifier for `html_elements`.

        Parameters
        ----------
        page_html : str
            Page from which `html_element` originates.
        selected_elements : list of HTMLElement
            The HTML elements for which a resource identifier is constructed.
        ignored_elements : list of HTMLElement
            The HTML elements that should not be selected by the identifier.
        structural_element : StructuralElement
            The structural element that the `html_elements` represent, e.g. LoginButton.
        driver : TorBrowserDriver
            The TorBrowserDriver necessary only for one AnalyzerMethod using Selenium to identify the elements.
            Overloading is not possible, and Multidispatching is not recommended in multithreaded programs, hence this
            questionable solution.

        Returns
        -------
        XPath or None
            The resource identifier with which all the `html_elements` and none of the `ignored_elements`
            are identified. Returns None if it was not possible to construct such an identifier.
        """
        common_classes = None

        outer_htmls_selected = [elt.outer_html for elt in selected_elements]
        for outer_html in outer_htmls_selected:
            soup = BeautifulSoup(outer_html, 'html.parser')

            # List of classes of the root html_element, or None if it has no class
            classes = soup.contents[0].get('class')

            if classes is None:
                # TODO: better way of dealing with the case the html_element has no classes
                #  maybe navigate down the html_element tree to search for elements that do have classes
                return None
            else:
                if common_classes is None:
                    common_classes = set(classes)
                else:
                    common_classes = common_classes.intersection(set(classes))

        outer_htmls_ignored = [elt.outer_html for elt in ignored_elements]
        for outer_html in outer_htmls_ignored:
            soup = BeautifulSoup(outer_html, 'html.parser')

            # List of classes of the root html_element, or None if it has no class
            classes = soup.contents[0].get('class')

            # Subtract all the classes from the ignored elements
            if classes is not None:
                common_classes = common_classes.difference(set(classes))

        if len(common_classes) == 0:
            return None
        else:
            list_common_classes = list(common_classes)
            remaining_classes = len(list_common_classes)
            xpath = "[@class='"
            for c in list_common_classes:
                remaining_classes -= 1
                if remaining_classes == 0:
                    xpath = xpath + c + "']"
                else:
                    xpath = xpath + c + "' and @class='"

            return XPath(xpath)

        # TODO: probably not a good idea to have an identifier that uses all the classes attached to the html element.
        #  instead we should somehow find a way to get the relevant class(es) out of the list
