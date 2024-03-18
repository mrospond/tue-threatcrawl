"""File containing the AnalyzerMethod3 class."""
from typing import List, Optional

from tbselenium.tbdriver import TorBrowserDriver

from database.util import DataContainer
from enums import StructuralElement
from trainer.abstract_analyzer import AbstractAnalyzer
from trainer.html_element import HTMLElement
from trainer.xpath import XPath
from trainer.xpath_except import XPathExcept
from trainer.xpath_helper_functions import combine_x_path_by_or
from lxml import etree
from enums.navigational_element import NavigationalElement
from enums.input_element import InputElement
from enums.data_element import DataElement
import re


class AnalyzerMethod3(AbstractAnalyzer):
    """Class for constructing resource identifiers for HTML elements.

    The algorithm is adapted from the following paper:
    Leotta, Maurizio, et al. "ROBULA+: An algorithm for generating robust XPath locators for web testing."
    Journal of Software: Evolution and Process 28.3 (2016): 177-204.
    """

    def __init__(self):
        self.priority_attributes = ['name', 'class', 'rel', 'title', 'alt', 'value']
        self.blacklisted_attributes = {'href', 'src', 'onclick', 'onload', 'tabindex', 'width', 'height', 'style',
                                       'size', 'maxLength', 'id'}

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
        # Do not use AnalyzerMethod3 for DataElements
        if isinstance(structural_element, DataElement):
            return None

        # Convert str into lxml HTML object
        html_obj = etree.HTML(page_html)
        try:
            return self.calculate_robust_xpath([elmnt.x_path for elmnt in selected_elements],
                                               [elmnt.x_path for elmnt in ignored_elements],
                                               html_obj, structural_element, max_iter=100)
        except IndexError:
            return None

    def calculate_robust_xpath(self, x_paths_selected_elements, x_paths_ignored_elements, html_obj,
                               structural_element, max_iter=100):
        """Calculate a robust XPath for a single element on a web page.

        Parameters
        ----------
        x_paths_selected_elements: list of str
            The XPaths of the selected elements.
        x_paths_ignored_elements: list of str
            The XPaths of the ignored elements.
        html_obj : lxml Element
            The lxml HTML object of the web page from which the element originates.
        max_iter : int, optional
            The maximum number of iterations that is performed of the calculation process.
        structural_element : StructuralElement
            The type of structural element for which an identifier is constructed.

        Returns
        -------
        ResourceIdentifier or None
            The XPath or XPathExcept identifier with which all the `html_elements` and none of the `ignored_elements`
            are identified. Returns None if it was not possible to construct such an identifier.
        """
        x_path_element = x_paths_selected_elements[0]
        x_path_rest_elements = x_paths_selected_elements[1:]
        rest_elements = [html_obj.xpath(x_path)[0] for x_path in x_path_rest_elements]

        ancestor_list = self.calculate_ancestor_list(x_path_element, html_obj)

        x_path_list = ['//*']
        sufficient_x_paths = []

        for _ in range(max_iter):
            if len(x_path_list) == 0:
                break
            current_x_path = x_path_list.pop(0)
            temp = []
            temp += self.transf_convert_star(current_x_path, ancestor_list)
            # temp += self.transf_add_id(current_x_path, ancestor_list)
            temp += self.transf_add_text(current_x_path, ancestor_list)
            temp += self.transf_add_attribute(current_x_path, ancestor_list)
            # temp += self.transf_add_attribute_set(current_x_path, ancestor_list)
            temp += self.transf_add_position(current_x_path, ancestor_list)
            temp += self.transf_add_level(current_x_path, ancestor_list)

            for x_path in temp:
                if not bool(re.search('[а-яА-Я]', x_path)):
                    (sufficient, identifier, count) = \
                        self.uniquely_identifies(x_path, ancestor_list[0], rest_elements, x_paths_ignored_elements,
                                                 html_obj, structural_element)
                    if sufficient:
                        sufficient_x_paths.append((identifier, count))
                    else:
                        x_path_list.append(x_path)

        if len(sufficient_x_paths) == 0:
            return None

        # print(sufficient_x_paths)
        (minimal_x_path, _) = min(sufficient_x_paths, key=lambda t: t[1])
        return minimal_x_path

    def uniquely_identifies(self, x_path, element, other_selected_elements, ignored_element_xpaths,
                            html_obj, structural_element):
        """Whether the selected elements are identified by the XPath.

        Parameters
        ----------
        x_path : str
            The XPath for identifying `element`.
        element : lxml Element
            The lxml Element that need to be uniquely identified.
        other_selected_elements : list of lxml Element
            The other elements selected by the user.
        ignored_element_xpaths : list of str
            The XPaths to elements that should not be identified.
        html_obj : lxml Element
            The lxml Element of the entire web page from which `element` originates.
        structural_element : StructuralElement
            The type of structural element for which an identifier is constructed.

        Returns
        -------
        (sufficient, identifier, count) : (bool, ResourceIdentifier or None, int)
            `sufficient` indicates whether the `x_path` identifies the `element` and `other_selected_elements`;
            `identifier` is the ResourceIdentifier, if `sufficient` is true, otherwise it is None'
            `count` indicates how bad the `x_path` is.
        """
        # print("Considering:", x_path)
        # print(x_path)
        elmnts = html_obj.xpath(x_path)
        # print(elmnts)
        # print(element)
        correct = len(elmnts) <= self.reasonable_number_of_elements(structural_element) and (element in elmnts)

        # Number of extra elements, not selected by the user, that are identified
        count = len(elmnts) - len(other_selected_elements) - 1
        for other_element in other_selected_elements:
            # print(other_element)
            correct = correct and (other_element in elmnts)

        xpaths_ignored_but_identified = []
        for ignored_element_xpath in ignored_element_xpaths:
            elmnt = html_obj.xpath(ignored_element_xpath)[0]
            found = False
            if elmnt in elmnts:
                count += 1000
                found = True
            for descendant in elmnt.iterdescendants():
                if descendant in elmnts:
                    count += 1000
                    found = True
            if found:
                xpaths_ignored_but_identified.append(ignored_element_xpath)

        if len(xpaths_ignored_but_identified) == 0:
            return correct, XPath('/html/body' + x_path), count
        elif correct:
            x_path_use = XPath('/html/body' + x_path)
            x_path_ignore = XPath(combine_x_path_by_or(xpaths_ignored_but_identified))
            return correct, XPathExcept(x_path_use, x_path_ignore), count
        else:
            return correct, None, count

    def calculate_ancestor_list(self, x_path_element, html_obj):
        """Calculate list of ancestors of an element.

        Parameters
        ----------
        x_path_element : str
            XPath to element of which to calculate the ancestor list.
        html_obj : lxml Element
            The HTML element that needs to be identified to get the ancestors of `x_path_element`.

        Returns
        -------
        list of lxml Element
            List of lxml Elements containing all ancestors including the element itself.
        """
        # Get ElementUnicodeResult based on x_path
        element = html_obj.xpath(x_path_element)[0]

        ancestors = [element]
        for ancestor in element.iterancestors():
            ancestors.append(ancestor)

        return ancestors

    def transf_convert_star(self, x_path, ancestor_list):
        """Replace the star (*) in the XPath which starts with "//*" with the tag name.

        Parameters
        ----------
        x_path : str
            The XPath expression start with "//*".
        ancestor_list : list of lxml Element
            List of lxml Elements containing all ancestors including the element itself.

        Returns
        -------
        list of str
            The list of XPaths with '//*' replaced by the tag names in ancestor_list.
        """
        x_path_list = []

        if (x_path.startswith("//*")):
            current_ancestor = self.get_current_ancestor(x_path, ancestor_list)
            x_path_list.append(x_path.replace("//*", "//" + current_ancestor.tag))

        return x_path_list

    def transf_add_id(self, x_path, ancestor_list):
        """Construct the XPath that contains id in the higher level of input XPath. For example, a XPath = "//td" with
        id = "name" will gives a new XPath = "//td[@id=‘name’]"

        Parameters
        ----------
        x_path : str
            The XPath str that does not contain predicates
        ancestor_list : list of lxml Element
            List of lxml Elements containing all ancestors including the element itself.

        Returns
        -------
        list of str
            The XPath list contains xpath which has id in one higher level of input XPath
        """
        x_path_list = []
        current_ancestor = self.get_current_ancestor(x_path, ancestor_list)

        if (not self.head_has_any_predicates(x_path)) and current_ancestor.attrib.get('id'):
            predicate = f"[@id='{current_ancestor.attrib.get('id')}']"
            x_path_list.append(self.add_predicate_to_head(x_path, predicate))

        return x_path_list

    def transf_add_text(self, x_path, ancestor_list):
        """Add text predicate to the current XPath level, if the corresponding element contains any text.

        Parameters
        ----------
        x_path : str
            The XPath to modify.
        ancestor_list : list of lxml Element
            The list of ancestors of the target element.

        Returns
        -------
        list of str
            A list containing only the modified XPath, or an empty list.
        """
        x_path_list = []
        current_ancestor = self.get_current_ancestor(x_path, ancestor_list)

        if not self.head_has_position_predicate(x_path) and not self.head_has_text_predicate(x_path):
            text_nodes = current_ancestor.xpath('text()')
            complete_text = ''.join(text_nodes)
            complete_text = complete_text.strip()

            if self.text_is_useful(complete_text):
                predicate = f'[text()[contains(.,\'{complete_text}\')]]'
                x_path_list.append(self.add_predicate_to_head(x_path, predicate))

        return x_path_list

    def transf_add_attribute(self, x_path, ancestor_list):
        """Return a new XPath with attributes added on its ancestor if it has attribute which is not contained in
        blacklisted_attributes

        Parameters
        ----------
        x_path : str
            The XPath to modify.
        ancestor_list : list of lxml Element
            The list of ancestors of the target element.

        Returns
        -------
        list of str
            A list containing only the modified XPath, or an empty list.
        """
        x_path_list = []
        current_ancestor = self.get_current_ancestor(x_path, ancestor_list)

        if not self.head_has_any_predicates(x_path):
            for attribute in self.priority_attributes:
                value = current_ancestor.attrib.get(attribute)
                if value is None:
                    continue
                if attribute in ["title", "alt"] and not self.text_is_useful(value):
                    continue
                value = value.strip()
                predicate = f"[@{attribute}='{value}']"
                x_path_list.append(self.add_predicate_to_head(x_path, predicate))

            for attribute, value in current_ancestor.attrib.items():
                if attribute not in self.priority_attributes and attribute not in self.blacklisted_attributes:
                    predicate = f"[@{attribute}='{value}']"
                    x_path_list.append(self.add_predicate_to_head(x_path, predicate))

        return reversed(x_path_list)

    def transf_add_position(self, x_path, ancestor_list):
        """Add the position of the ancestor of the given x_path if x_path has an ancestor.

        Parameters
        ----------
        x_path : str
            The XPath to modify.
        ancestor_list : list of lxml Element
            The list of ancestors of the target element.

        Returns
        -------
        list of str
            A list containing only the modified XPath, or an empty list.

        """
        x_path_list = []
        N = self.calculate_level_of_xpath(x_path)
        current_ancestor = ancestor_list[N]
        if not self.head_has_position_predicate(x_path):
            position = 1
            if N + 1 < len(ancestor_list):
                if x_path.startswith('//*'):
                    parent_of_ancestor = ancestor_list[N+1]
                    position = parent_of_ancestor.getchildren().index(current_ancestor) + 1
                else:
                    parent_of_ancestor = ancestor_list[N+1]
                    for ancestor_element in parent_of_ancestor.getchildren():
                        if current_ancestor == ancestor_element:
                            break
                        if current_ancestor.tag == ancestor_element.tag:
                            position += 1
                predicate = '[' + str(position) + ']'
                new_xpath = self.add_predicate_to_head(x_path, predicate)
                x_path_list.append(new_xpath)

        return x_path_list

    def transf_add_attribute_set(self, x_path, ancestor_list):
        # TODO: Maybe implement
        return []

    def transf_add_level(self, x_path, ancestor_list):
        """"Add level of x_path by add '//*' at the top of x_path if the level of xpath is smaller than
        the length of ancestor_list

        Parameters
        ----------
        x_path : str
            The XPath to modify.
        ancestor_list : list of lxml Element
            The list of ancestors of the target element.

        Returns
        -------
        list of str
            A list containing only the modified XPath, or an empty list.
        """
        x_path_list = []
        if self.calculate_level_of_xpath(x_path) < len(ancestor_list) - 1:
            x_path_list.append('//*' + x_path[1:])
        return x_path_list

    def get_current_ancestor(self, x_path, ancestor_list):
        """Return the ancestor lxml element of given x_path

        Parameters
        ----------
        x_path : str
            The XPath to modify.
        ancestor_list : list of lxml Element
            The list of ancestors of the target element.

        Returns
        -------
        lxml Element
            The ancestor lxml Element of the given x_path.
        """
        N = self.calculate_level_of_xpath(x_path)
        return ancestor_list[N]

    def calculate_level_of_xpath(self, x_path):
        """Returns the level of given xpath

        Parameters
        ----------
        x_path : str
            The XPath to modify.

        Returns
        -------
        int
            The level of the given x_path
        """
        pieces = x_path.split('/')
        level = -1

        for piece in pieces:
            if piece != '':
                level += 1

        return level

    def head_has_any_predicates(self, x_path):
        """Return whether `x_path` has any predictates, for example, have format like '//class[@a = 0]'

        Parameter
        ---------
        x_path : str
            The XPath to modify.

        Returns
        -------
        boolean
            Whether `x_path` has any predictates
        """
        return '[' in x_path.split('/')[2]

    def head_has_position_predicate(self, x_path):
        """Return whether `x_path` has any position predictates, for example, have format like '//div[3]'

        Parameter
        ---------
        x_path : str
            The XPath to modify.

        Returns
        -------
        boolean
            Whether `x_path` has any position predictates
        """
        head = x_path.split('/')[2]
        return bool(re.search('[\\[0-9\\]]', head))

    def head_has_text_predicate(self, x_path):
        """Return whether `x_path` has any text predictates, for example, have format like '//Word[text()='July']'

        Parameter
        ---------
        x_path : str
            The XPath to modify.

        Returns
        -------
        boolean
            Whether `x_path` has any text predictates
        """
        return 'text()' in x_path.split('/')[2]

    def add_predicate_to_head(self, x_path, predicate):
        """Return a new XPath str with predicate added in the head

        Parameter
        ---------
        x_path : str
            The XPath to modify.

        Returns
        -------
        str
            A new XPath str with predicate added in the head
        """
        splitXPath = x_path.split('/')
        splitXPath[2] += predicate
        return '/'.join(splitXPath)

    def text_is_useful(self, text):
        """Return whether the text in XPath is useful.

        If the text contains quatation mark and number, or if the text is too long (more than 50 characters),
        then the text will be considered not useful.

        Parameter
        ---------
        text : str
            The text waited to check whether it is useful.

        Returns
        -------
        boolean
            Whether the given text is useful.
        """

        if text is None or text == '':
            return False
        else:
            return not (len(text) > 50 or "'" in text or '"' in text or any(char.isdigit() for char in text))

    # def powerset(self, iterable):
    #     s = list(iterable)
    #     return chain.from_iterable(combinations(s, r) for r in range(len(s)+1))

    def reasonable_number_of_elements(self, structural_element):
        """Whether the number of elements identified by this resource identifier is reasonable.

        Parameters
        ----------
        structural_element : StructuralElement
            The type of structural element that this resource identifier is supposed to identify.

        Returns
        -------
        bool
            Whether the number of elements identified by this resource identifier is reasonable.
        """
        if isinstance(structural_element, InputElement):
            return 1
        elif isinstance(structural_element, NavigationalElement):
            return 5
        elif isinstance(structural_element, DataElement):
            return 100
        else:
            raise RuntimeError("Unknown structural element type: " + str(type(structural_element)))
