"""File containing the PageStructure class."""
from dataclasses import dataclass
from enums.page_type import PageType
from enums.structural_element import StructuralElement
from trainer.resource_identifier import ResourceIdentifier
from typing import Dict


@dataclass
class PageStructure:
    """Class containing the structure of a web page.

    page_type : PageType
        The type of the page.
    identifiers : Dict[StructuralElement, ResourceIdentifier]
        For every identified `StructuralElement` on the web page, the associated trained `ResourceIdentifier`.
    """
    page_type: PageType
    identifiers: Dict[StructuralElement, ResourceIdentifier]
    javascript: str
