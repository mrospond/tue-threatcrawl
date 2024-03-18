from enums import StructuralElement
from enums import DataElement
from enums import NavigationalElement
from enums import PageType
from enums import InputElement
from datetime import datetime
from trainer.html_class import HTMLClass
from trainer.resource_identifier import ResourceIdentifier
from bs4 import BeautifulSoup
from utils import Logger
import typing as t


def strip_tags(strings: t.Union[t.List[str], str]) -> t.List[t.List[str]]:
    """Strips HTML tags from a string

    Parameters
    ----------
    strings : t.Union[t.List[str], str]
        String(s) to strip from HTML tags. All strings are assumed to contain pairs of HTML tags.

    Returns
    -------
    t.List[t.List[str]]
        List of list of strings stripped from HTML tags. The content of each string is stored in the top most list, with
        a list of strings as elements which represent the contents that remain of the string after stripping a tag. To
        support stripping multiple tags, the contents of each individual tag is stored as an element in that list. An
        example is given in the notes.

    Notes
    -----
    Let's say you have a list of strings to strip, being ['<h1>Header here</h1>', '<span, class='first span'>Span
    content <span, class='nested span'>Nested span content</span></span>']. The result will be [['Header here'],
    ['Span content', 'Nested span content']].
    """

    if not isinstance(strings, list) and isinstance(strings, str):
        strings = [strings]
    elif not all(isinstance(elm, str) for elm in strings):
        raise ValueError("Not all elements of the list are strings!")

    out = []
    for string in strings:
        soup = BeautifulSoup(string, "html.parser")
        stripped = [text for text in soup.stripped_strings]
        out.append(stripped)

    return out


def convert_types(strings: t.Union[t.List[t.List[str]], t.List[str]], element: StructuralElement,
                  page_type: PageType) -> list:
    """Converts lists of str to the right list of datatype based on the StructuralElement

    Parameters
    ---------
    strings : list of str
        List of strings to be converted.
    element : StructuralElement
        StructuralElement that the list belongs to. Determines to what type it will be converted.
    page_type : PageType
        Type of page that the StructuralElement belongs to. Should only be relevant for DataElement.ThreadTitle.

    Returns
    -------
    list of any
        List of the corresponding datatype based on StructuralElement.

    Raises
    ------
    ValueError
        If `strings` is not a list or an element is not a string, if `element` is not an instance of a StructuralElement
        subclass or if the elements of `string` are not valid ISO8601 strings if the resulting datatype must be
        datetime based on `element`.
    NotImplementedError
        If `element` is an instance of NavigationalElement that requires an XPath. Because those are special strings
        with special formatting requirements, we do not have all the information required here. Hence it is not
        supported to convert to an XPath string here.

    Notes
    -----
    The datatype conversion is hard-coded and must be changed if more StructuralElements are added or the expected
    datatypes are changed. This must not only be changed here but also in other modules.
    """

    if not isinstance(strings, list):
        raise ValueError("The list of strings is not a list!")
    elif not all(isinstance(elm, str) for elm in strings) and not all(isinstance(elm, list) for elm in strings):
        raise ValueError("Not all elements of the list are strings or lists!")
    elif not all(isinstance(elm, str) for elm in strings) and all(isinstance(elm, list) for elm in strings) \
            and not all(isinstance(elm, str) for s in strings for elm in s):
        raise ValueError("Not all elements of the list of the list are strings!")
    elif len(strings) == 0:
        # If we get an empty list return an empty list
        return []

    if isinstance(strings[0], str):
        single_list = True
    else:
        single_list = False

    if isinstance(element, DataElement):
        datatype = get_type(element, page_type=page_type)
        if single_list:
            if isinstance(datatype, str):
                # Are already strings so do not need to be converted
                return strings
            elif isinstance(datatype, int):
                # Convert each string to an int
                filtered = _filter_numerics(strings)
                out = []
                for i in range(0, len(filtered)):
                    if filtered[i] == "":
                        continue
                    else:
                        out.append(int(filtered[i]))
                return out
            elif isinstance(datatype, datetime):
                # Convert each string to datetime, under the assumption that the strings are ISO8601 formatted.
                return [datetime.fromisoformat(string) for string in strings]
        else:
            out = []
            for elm in strings:
                if isinstance(datatype, str):
                    # Are already strings so append with new lines to convert to single tier list
                    out_string = ""
                    for e in elm:
                        out_string += e + " \n "
                    out.append(out_string)
                elif isinstance(datatype, int):
                    # Convert each string to an int
                    outs = _filter_numerics(elm)
                    out_list = []
                    for o in outs:
                        if o != '':
                            try:
                                out_list.append(int(o))
                            except ValueError:
                                out_list.append(o)

                    if not out_list:
                        out_list.append(0)  # Setting to a default value to not make everything crash

                    out.append(out_list)
                elif isinstance(datatype, datetime):
                    # Convert each string to datetime, under the assumption that the strings are ISO8601 formatted.
                    out.append([datetime.fromisoformat(e) for e in elm])
            return out
    elif isinstance(element, NavigationalElement):
        if isinstance(get_type(element), ResourceIdentifier):
            # ResourceIdentifier indicates XPath, which is a special string which is not supported here.
            raise NotImplementedError
    elif isinstance(element, StructuralElement):
        raise ValueError("The StructuralElement is an instance of the abstract class!")
    else:
        raise ValueError("The StructuralElement is no instance of StructuralElement or its subclasses!")
    raise NotImplementedError


def get_type(element: StructuralElement, page_type: PageType = None) -> t.Any:
    """Get the datatype associated with a StructuralElement

    Parameters
    ---------
    element : StructuralElement
        The StructuralElement to get the associated datatype from.
    page_type : PageType, optional
        Type of page for which we need a StructuralElement. Is only relevant if `element` is DataElement.ThreadTitle.

    Returns
    ------
    any
        The associated datatype. Could be anything so be aware!

    Raises
    ------
    ValueError
        If `element` is not an instance of a subclass of StructuralElement.
    NotImplementedError
        If `element` is a valid argument but has no associated datatype.
    """

    if not isinstance(element, StructuralElement):
        raise ValueError(str(element) + " is not an instance of StructuralElement")
    if not isinstance(element, DataElement) and not isinstance(element, NavigationalElement) and \
            not isinstance(element, InputElement):
        raise ValueError(str(element) + " is an instance of the abstract StructuralElement??")

    strs = [DataElement.AuthorUsername, DataElement.AuthorEmail, DataElement.ThreadTitle, DataElement.ThreadSection,
            DataElement.PostContent]
    ints = [DataElement.AuthorNrOfPosts, DataElement.AuthorPopularity]
    dates = [DataElement.AuthorRegistrationDate, DataElement.ThreadAge, DataElement.PostDate]
    xpath = [NavigationalElement.HomeButton, NavigationalElement.NextPageButton, NavigationalElement.PreviousPageButton,
             NavigationalElement.LoginButton, InputElement.UsernameInput, InputElement.PasswordInput,
             DataElement.ThreadTitle, DataElement.SectionTitle, DataElement.SubsectionTitle,
             NavigationalElement.FirstThreadPageButton, InputElement.SubmitLoginButton]

    if element == DataElement.ThreadTitle:
        if page_type == PageType.ThreadPage:
            return str()
        else:
            return HTMLClass(["test"])

    if element in strs:
        return str()
    elif element in ints:
        return int()
    elif element in dates:
        return datetime.today()
    elif element in xpath:
        return HTMLClass(["test"])
    else:
        raise NotImplementedError(str(element) + " has not been mapped to a datatype yet :(")


def strip_list_with_checks(value: t.Union[t.List[t.Any], t.List[t.List[t.Any]]], key: t.Any,
                           page_type: PageType) -> t.List[str]:
    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
        return strip_list(value, isinstance(get_type(key, page_type), str))
    else:
        return value


def strip_list(list_of_lists: t.List[t.List[t.Any]], string: bool) -> t.List[t.Any]:
    """From list of lists, strip the inner list and return a single list.

    If for example we have the following list of lists: [[x], [y], [z]]. This function converts it into [x, y, z].

    Parameters
    ----------
    list_of_lists : t.List[t.List[t.Any]]
        List of lists to be converted into a single list.
    string : bool
        Whether the contents of the list is a string and hence multiple elements in the inner list should be
        concatenated.

    Returns
    -------
    t.List[t.Any]
        Single list, conserving the original order.
    """
    out_list = []
    for l in list_of_lists:
        if not l:
            out_list.append(None)

        if string:
            Logger.log("debug", "Converting {} into a single string".format(l))
            out_string = ""

            for elm in l:
                out_string += " " + elm

            Logger.log("debug", "Result {}".format(out_string))
            out_list.append(out_string)
        else:
            for elm in l:
                out_list.append(elm)
    return out_list


def _filter_numerics(strings: t.List[str]) -> t.List[str]:
    """Filters the given list of strings on numerical characters.

    This function is used to filter out numbers (including negative numbers) from a list of strings. Primarily used for
    string to integer conversion.

    Parameters:
    -----------
    strings : list of str
        List of strings to filter on numerics.

    Returns
    -------
    list of str
        List of strings which is stripped from non-numerical characters.
    """
    out_list = []
    for string in strings:
        elm = ""
        for i in range(len(string)):
            if string[i].isnumeric():
                elm += string[i]
            elif string[i] == '-' and i + 1 < len(string):
                if string[i + 1].isnumeric():
                    elm += string[i]
        out_list.append(elm)
    return out_list


def verify_struct(structure : t.Any):
    """Verify that the given structure is a proper one.

    Parameters
    ----------
    structure : any
        Structure to be checked whether it is in the right format

    Raises
    ------
    ValueError
        If the structure is not in the right format
    """
    if not isinstance(structure, dict):
        raise ValueError("The passed platform structure is not a dictionary!")
    # elif structure == {}:
    #     raise ValueError("The passed platform structure is an empty dictionary!")
    elif not all(isinstance(elm, PageType) for elm in structure.keys()):
        raise ValueError("Not all keys of the platform structure are PageTypes!")
    elif not all(isinstance(elm, dict) for elm in structure.values()):
        raise ValueError("Not all values of the platform structure are dictionaries!")
    elif not all(isinstance(elm, ResourceIdentifier) for d in structure.values() for elm in d.values()):
        raise ValueError("Not all values of the platform structure dictionary are ResourceIdentifiers!")
    elif not all(isinstance(elm, StructuralElement) for d in structure.values() for elm in d.keys()):
        raise ValueError("Not all keys of the platform structure dictionary are StructuralElements!")
