"""File containing the xpath helper functions which is useful for analyzer method 2."""
# from difflib import SequenceMatcher
# import itertools
from lxml.html import document_fromstring
from selenium.webdriver.remote.webelement import WebElement
from tbselenium.tbdriver import TorBrowserDriver

from utils import Logger
import typing as t


def calculate_common_xpath_of_pair(xpath_1: str, xpath_2: str) -> str:
    """Returns the common XPath string of a pair of XPaths.

    Parameters
    ----------
    xpath_1: str
        An XPath string to be compared with `xpath_2`
    xpath_2: str
        An XPath string to be compared with `xpath_1`.

    Return
    ------
    result_xpath: str
        Common XPath for the given pair of XPaths.
    """
    element1_splitted = xpath_1.split("/")
    element2_splitted = xpath_2.split("/")

    # Make the depths of two xpath are the same
    element1_splitted = element1_splitted[:len(element2_splitted)]
    element2_splitted = element2_splitted[:len(element1_splitted)]

    result_xpath_element = []
    length_element_list = len(element1_splitted)
    for index in range(0, length_element_list):
        if element1_splitted[index] == element2_splitted[index]:
            result_xpath_element.append(element1_splitted[index])
        else:
            if "[" in element1_splitted[index]:
                # The mismatch handled here is like:
                # div[4] <---> div[22]
                element1_splitted[index] = element1_splitted[index].split("[")[0]
            if "[" in element2_splitted[index]:
                element2_splitted[index] = element2_splitted[index].split("[")[0]
            if element1_splitted[index] == element2_splitted[index]:
                result_xpath_element.append(element1_splitted[index])
    result_xpath = "/".join(map(str, result_xpath_element))
    return result_xpath


def calculate_common_xpath(x_paths: t.List[str]) -> str:
    """Returns common XPath string for a list of provided XPaths.

    Parameters
    ----------
    x_paths : list of str
        The list of XPath expressions.

    Return
    ------
    str
        The common XPath expression for `x_paths`.

    Examples
    --------
    >>> calculate_common_xpath(['/html/body/div[1]/a[3]', '/html/body/div[2]/a[5]', '/html/body/div[5]/a[1]'])
    '/html/body/div/a'

    >>> calculate_common_xpath(['/html/body/div[1]/a[3]', '/html/body/div[1]/div[1]/a[1]', '/html/body/div[5]/a[1]'])
    '/html/body/div'
    """
    if len(x_paths) == 0:
        raise RuntimeError("No XPaths were provided.")

    working = x_paths.copy()
    while len(working) > 1:
        # We compare the first XPath, which we call the pivot, with all the others
        pivot = working[0]
        common_xpaths = set()
        for x_path in working[1:]:
            common_xpaths.add(calculate_common_xpath_of_pair(pivot, x_path))
        working = list(common_xpaths)
    if not working[0].startswith('/'):
        return "//" + working[0]
    else:
        return working[0]


def verify_common_x_path(common_path: str, prev_common_path: str, html: str) -> bool:
    """ Verifies that the common XPath `common_path` gives the same results as the previously identified common XPath.

    Parameters
    ----------
    common_path : str
        String representation of the supposed common XPath.
    prev_common_path : str
        String representations of the previous common XPath.
    html:
        HTML of the page.

    Returns
    -------
    bool
        If the number of identified elements using both XPaths is the same.
    """

    # Verify that only the supplied XPaths are returned and not more
    doc = document_fromstring(html)
    tree = doc.getroottree()
    results = tree.findall(common_path)
    prev_results = tree.findall(prev_common_path)

    if len(results) == len(prev_results):
        return True
    else:
        Logger.log("Trainer", "Mismatch in lengths! {} is not equal to {}".format(len(results), len(prev_results)))
        return False


def combine_x_path_by_or(x_paths: t.List[str]) -> str:
    """Combine multiple XPaths into one, using a logical OR.

    Parameters
    ----------
    x_paths : list of str
        The XPaths that need to be combined.

    Return
    ------
    str
        The combined XPath.
    """
    if len(x_paths) == 0:
        raise RuntimeError("No XPaths were provided.")
    working = x_paths.copy()
    result = x_paths[0]
    for single_xpath in working[1:]:
        result = result + " | " + single_xpath
    return result


def calculate_xpath(element: WebElement, driver: TorBrowserDriver) -> str:
    # Source based on FourTwoOmega's reply
    # https://stackoverflow.com/questions/4176560/webdriver-get-elements-xpath
    xpath = driver.execute_script(
        "gPt=function(c){if(c.id!==''){return\"id('\"+c.id+\"')\"}if(c===document.body){return c.tagName}var "
        "a=0;var e=c.parentNode.childNodes;for(var b=0;b<e.length;b++){var d=e[b];if(d===c){return gPt(c."
        "parentNode)+'/'+c.tagName.toLowerCase()+'['+(a+1)+']'}if(d.nodeType===1&&d.tagName===c.tagName)"
        "{a++}}};return gPt(arguments[0]);", element)
    if xpath.startswith("BODY"):
        xpath = xpath[4:len(xpath)]
        xpath = "/html/body" + xpath
    return xpath


def calculate_full_xpath(element: WebElement, driver: TorBrowserDriver) -> str:
    # https://stackoverflow.com/questions/43003935/get-absolute-xpath-of-web-element
    return driver.execute_script(
        """function getAbsoluteXPath(element) {
            var comp, comps = [];
            var parent = null;
            var xpath = '';
            var getPos = function(element) {
                var position = 1,
                    curNode;
                if (element.nodeType == Node.ATTRIBUTE_NODE) {
                    return null;
                }
                for (curNode = element.previousSibling; curNode; curNode = curNode.previousSibling) {
                    if (curNode.nodeName == element.nodeName) {
                        ++position;
                    }
                }
                return position;
            };
        
            if (element instanceof Document) {
                return '/';
            }
        
            for (; element && !(element instanceof Document); element = element.nodeType == Node.ATTRIBUTE_NODE ? element.ownerElement : element.parentNode) {
                comp = comps[comps.length] = {};
                switch (element.nodeType) {
                    case Node.TEXT_NODE:
                        comp.name = 'text()';
                        break;
                    case Node.ATTRIBUTE_NODE:
                        comp.name = '@' + element.nodeName;
                        break;
                    case Node.PROCESSING_INSTRUCTION_NODE:
                        comp.name = 'processing-instruction()';
                        break;
                    case Node.COMMENT_NODE:
                        comp.name = 'comment()';
                        break;
                    case Node.ELEMENT_NODE:
                        comp.name = element.nodeName;
                        break;
                }
                comp.position = getPos(element);
            }
        
            for (var i = comps.length - 1; i >= 0; i--) {
                comp = comps[i];
                xpath += '/' + comp.name.toLowerCase();
                if (comp.position !== null) {
                    xpath += '[' + comp.position + ']';
                }
            }
            return xpath;
        }
        
        return getAbsoluteXPath(arguments[0]);""", element)

