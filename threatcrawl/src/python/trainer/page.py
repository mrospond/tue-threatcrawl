"""File containing the PageType class."""
from dataclasses import dataclass


@dataclass
class Page:
    """Class containing the content and url of a web page.

    html : str
        The HTML content of the page.
    url : str
        The URL of the page.
    """
    html: str
    url: str
