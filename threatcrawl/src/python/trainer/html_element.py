"""File containing the HTMLElement class."""
from dataclasses import dataclass


@dataclass
class HTMLElement:
    """Class representing an HTML element by its outer HTML, and its XPath which locates
    it in the web page the elements originates from."""
    outer_html: str
    x_path: str
