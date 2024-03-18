"""File containing the AnalyzerMethod2 class."""
from typing import List, Optional, Union

from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer
from trainer.abstract_analyzer import AbstractAnalyzer
from trainer.html_element import HTMLElement
from trainer.xpath import XPath
from trainer.xpath_except import XPathExcept
from trainer.xpath_helper_functions import calculate_common_xpath, combine_x_path_by_or, verify_common_x_path
from enums import DataElement, StructuralElement
from utils import Logger
from re import search


class AnalyzerMethod2(AbstractAnalyzer):
    """Class for constructing resource identifiers for html elements with implemented method 2."""

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
        ResourceIdentifier or None
            The XPath or XPathExcept identifier with which all the `html_elements` and none of the `ignored_elements`
            are identified. Returns None if it was not possible to construct such an identifier.
        """
        x_paths_selected = [elt.x_path for elt in selected_elements]
        x_paths_ignored = [elt.x_path for elt in ignored_elements]

        x_path_use = XPath(calculate_common_xpath(x_paths_selected))

        if structural_element == DataElement.SectionTitle or structural_element == DataElement.SubsectionTitle or \
                structural_element == DataElement.ThreadTitle:
            x_path = x_path_use.x_path
            x_path_regex = "/a([.*?])??"
            res = search(x_path_regex, x_path)

            # If there is no match for an a element in the XPath, ignore the following code that forces the use of an a
            # element.
            if res is not None:
                end_idx = res.end()
                new_x_path = x_path[8:end_idx]
                if not verify_common_x_path(new_x_path, x_path[8:], page_html):
                    Logger.log("trainer", "Analyzer method 2 Verification of new common path failed")
                    # return None
                else:
                    x_path_use = XPath(x_path[:end_idx])

        if len(x_paths_ignored) == 0:
            return x_path_use
        else:
            x_path_remove = XPath(combine_x_path_by_or(x_paths_ignored))
            return XPathExcept(x_path_use, x_path_remove)
