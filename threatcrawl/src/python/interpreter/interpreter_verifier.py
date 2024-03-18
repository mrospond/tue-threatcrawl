"""Interpreter class to verify the trained structure works, and not just on the given specific version of the page but
also on fresh ones."""

import typing as t
from enums import PageType, StructuralElement
from trainer import ResourceIdentifier
from .interpreter_utils import verify_struct
from utils import Logger


class InterpreterVerifier:
    """Class that verifies the structure works on multiple versions of the same page. Meaning it checks whether
    everything that could be found on the page used for training can also be found on a freshly retrieved instance of
    the same page (obtained by reloading the page or opening the same page in a new window).

    Parameters
    ----------
    structure : dict<PageType, dict<StructuralElement, ResourceIdentifier>>
        Trained structure to verify.

    Attributes
    ----------
    __structure : dict<PageType, dict<StructuralElement, ResourceIdentifier>>
        Stored structure to verify.
    """
    def __init__(self, structure: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        self.__structure = structure

    def verify(self, original_page: str, new_page: str, page_type: PageType) -> bool:
        """Verify whether the current platform structure works on both the page used to train with and a newly retrieved
        copy of the same page.

        Parameters
        ----------
        original_page : str
            HTML of the page used to train with.
        new_page : str
            HTML of the fresh copy of the page used to train with.
        page_type : PageType
            The type of page that this page is.

        Returns
        -------
        bool
            Whether the same tags could be found with the current platform structure on both pages. True if so, False if
            not.
        """
        for element, ri in self.__structure[page_type].items():
            og_results = ri.get_elements(original_page)
            new_results = ri.get_elements(new_page)

            Logger.log("interpreter", "Original results: {}".format(og_results))
            Logger.log("interpreter", "New results: {}".format(new_results))

            if og_results != new_results:
                return False

        return True

    @property
    def structure(self) -> t.Union[t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]], None]:
        """Get the structure that InterpreterData uses.

        Returns
        ------
        t.Union[t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]], None]
            The structure used by InterpreterData, None if improperly initialised."""
        return self.__structure

    @structure.setter
    def structure(self, structure: t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]):
        """Set the structure that InterpreterVerifier uses.

        Parameters
        ------
        structure : t.Dict[PageType, t.Dict[StructuralElement, ResourceIdentifier]]
            The structure to be used by InterpreterVerifier."""
        verify_struct(structure)
        self.__structure = structure
